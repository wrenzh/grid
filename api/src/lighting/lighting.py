from typing import Optional
from serial import Serial
from find_port import portname
from fastapi import HTTPException, Path, Query, Body, APIRouter, WebSocket
from pydantic import BaseModel, Field, field_validator
from ipaddress import IPv4Address
from typing import Annotated
import asyncio
import time

router = APIRouter(prefix="/api/lighting", tags=["lighting"])


def __decode__(msg: bytes or bytearray, cmd: str):
    """
    Decode the serial command and return the data field

    Transmitter response message format

    ## + Transmitter address + : + Command + : + Data + CR + CR + LF

    1. Fixed 2 bytes ##
    2. Transmitter address (8 bytes long) such as 048BE6E1
    3. Transmitter address, command and data are joined together with :
    4. There is a carriage return at the end of data field

    If argument `raw` is True, the data field will be returned in bytes instead of string
    """
    if isinstance(msg, bytes):
        msg = bytearray(msg)

    fields = msg.split(b":")

    if len(fields) != 3:
        raise LightingException(f"Expect 3 fields separated by :, got {len(fields)}")

    if not fields[0].startswith(b"##"):
        raise LightingException(
            f"Expect response to start with ##, got {fields[0].decode('ascii')}"
        )

    addr = fields[0][2:].decode("ascii")

    if fields[1] != cmd.encode("ascii"):
        raise LightingException(
            f"Incorrect command. Expect {cmd}, got {fields[1].decode('ascii')}"
        )

    data_raw = fields[2].rstrip()
    if not raw:
        data = fields[2].rstrip().decode("ascii")
    else:
        data = None

    return addr, data, data_raw


def __encode__(addr: str, cmd: str, data: Optional[str | bytes] = None) -> bytes:
    """
    Encode the serial command to the transmitter command format

    @@ + Transmitter address + : + Command + : + Data(optional) + CR
    """
    msg = "@@" + addr + ":" + cmd
    if data is None:
        return (msg + "\n").encode("ascii")
    elif isinstance(data, str):
        return (msg + ":" + data + "\n").encode("ascii")
    else:
        msg_bytes = (msg + ":").encode("ascii") + data + "\n".encode("ascii")
        return msg_bytes


class LightingException(Exception):
    pass


def send(lora: Serial, addr: str, cmd: str, data: Optional[str | bytes] = None) -> None:
    """Helper function for sending message through LoRa"""
    lora.write(__encode__(addr, cmd, data))


def receive(lora: Serial) -> bytes:
    """Helper function for getting response through LoRa"""
    res = lora.readline()
    if len(res) == 0:
        raise HTTPException(status_code=500, detail="LoRa response timeout")
    return res


def decode(res: bytes | bytearray, cmd: str, raw: bool = False):
    """Helper function for obtaining data from LoRa response"""
    busy = [
        e.encode("ascii") for e in ["WHUSEING", "WHBUSY", "TOPOBUSY", "STAGROUPBUSY"]
    ]
    if any([res.startswith(b) for b in busy]):
        raise HTTPException(status_code=503, detail="Transmitter busy")

    try:
        (addr, data) = __decode__(res, cmd, raw)
    except LightingException as e:
        raise HTTPException(status_code=500, detail=str(e))

    return addr, data


class ControlMode(BaseModel):
    """Data model for transmitter external control modes"""

    analog: bool
    button: bool
    modbus: bool
    bacnet: bool
    debug: bool


class Dimming(BaseModel):
    """Data model for 3 channel dimming signals, dimming values are x10"""

    dimming_levels: list[int] = Field(None, min_length=3, max_length=3)


class StartupControl(BaseModel):
    """
    Data model for startup control, ramp_up_duration feature is removed
    Note default_dimming is x1 instead of x10
    """

    is_enabled: bool
    default_dimming: int = Field(None, ge=0, le=100)


class IpConfig(BaseModel):
    """
    Data model for IP address, netmask and gateway
    """

    dynamic: bool
    address: IPv4Address
    netmask: IPv4Address
    gateway: IPv4Address


class PowerMeter(BaseModel):
    """
    Data model for power meter
    """

    header: int = Field(None, ge=0x55, le=0x55)
    irms: int
    vrms: int
    pulse_count: int
    temperature_int: int
    temperature_ext: int
    checksum: int


class STAStatus(BaseModel):
    """
    Data model for STA status report
    """

    serial_number: str = Field(min_length=12, max_length=12)
    firmware_version: str = Field(min_length=6, max_length=6)
    dimming: Dimming
    dimming_style: int
    power_meter: PowerMeter


@router.get("/list_cco")
def list_cco(
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5
):
    """
    List the transmitter serial numbers connected in the LoRa network
    """
    with Serial(portname, timeout=timeout) as lora:
        cco_uid = "FFFFFFFF"
        cmd = "CCO_UID"

        send(lora, cco_uid, cmd)
        res = receive(lora)
        (addr, _) = decode(res, cmd)

        return {"address": addr}


@router.get("/{cco_uid}/control_mode")
def get_control_mode(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port timeout in seconds")
    ] = 0.5,
):
    """
    Get the transmitter control mode, 1 means on and 0 means off.
    The sequence is in 0-10V, Button, Modbus/RTU, BACnet/IP and RS232 Debug.
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "GETTYPE"

        send(lora, cco_uid, cmd)
        res = receive(lora)
        (_, data) = decode(res, cmd)

        analog = data[0] == "1"
        button = data[2] == "1"
        modbus = data[4] == "1"
        bacnet = data[6] == "1"
        debug = data[8] == "1"

        return ControlMode(
            analog=analog, button=button, modbus=modbus, bacnet=bacnet, debug=debug
        )


@router.put("/{cco_uid}/control_mode")
def set_control_mode(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    control_mode: Annotated[
        ControlMode, Body(title="Transmitter external control mode")
    ],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port timeout in seconds")
    ] = 0.5,
):
    """
    Set the transmitter control mode, true means on and false means off
    The sequence is in 0-10V, Button, Modbus/RTU, BACnet/IP and RS232 Debug.
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "SETTYPE"
        data_list = [" "] * 5
        data_list[0] = "1" if control_mode.analog else "0"
        # button mode is always enabled
        data_list[1] = "1"
        data_list[2] = "1" if control_mode.modbus else "0"
        data_list[3] = "1" if control_mode.bacnet else "0"
        data_list[4] = "1" if control_mode.debug else "0"
        data = " ".join(data_list)

        send(lora, cco_uid, cmd, data)

        # Wait until the settings are applied
        time.sleep(0.5)
        res = receive(lora)

        (_, res_data) = decode(res, cmd)

        if data != res_data:
            raise HTTPException(
                status_code=500, detail="Dimming mode response does not match"
            )


@router.post("/{cco_uid}/reset_control_mode")
def reset_control_mode(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Reset the control modes and force the transmitter to use 0-10V dimming.
    The transmitter will follow digital command if receiving digital signals even after this command.
    """
    set_control_mode(
        cco_uid,
        ControlMode(analog=True, button=True, modbus=True, bacnet=True, debug=True),
        timeout,
    )
    with Serial(portname, timeout=timeout) as lora:
        cmd = "RESET10V"
        send(lora, cco_uid, cmd)


@router.put("/{cco_uid}/dim_single/{sta_uid}")
def dim_single(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    sta_uid: Annotated[
        str, Path(title="Adapter serial number", min_length=12, max_length=12)
    ],
    dimming: Annotated[Dimming, Body(title="Three channel dimming level")],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Enable and set the single fixture dimming level
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "DIMALL3"
        # Single dimming data is in raw hex format instead of ascii
        # Last byte of 0x04 means enabling single dimming
        data = (
            b"".join(
                [d.to_bytes(length=2, byteorder="big") for d in dimming.dimming_levels]
            )
            + bytes.fromhex(sta_uid)
            + int.to_bytes(0x04, length=1, byteorder="big")
        )
        # There is no ":" separator between cmd and data
        temp = __encode__(cco_uid, cmd).rstrip()
        lora.write(temp + data + b"\n")


@router.post("/{cco_uid}/disable_dim_single/{sta_uid}")
def disable_dim_single(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    sta_uid: Annotated[
        str, Path(title="Adapter serial number", min_length=12, max_length=12)
    ],
    dimming: Annotated[Dimming, Body(title="Three channel dimming level")] = Dimming(
        dimming_levels=[0, 0, 0]
    ),
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    with Serial(portname, timeout=timeout) as lora:
        cmd = "DIMALL3"
        # Single dimming data is in raw hex format instead of ascii
        # Last byte of 0x05 means disabling single dimming
        data = (
            b"".join(
                [d.to_bytes(length=2, byteorder="big") for d in dimming.dimming_levels]
            )
            + bytes.fromhex(sta_uid)
            + int.to_bytes(0x05, length=1, byteorder="big")
        )
        # There is no ":" separator between cmd and data
        temp = __encode__(cco_uid, cmd).rstrip()
        lora.write(temp + data + b"\n")


@router.get("/{cco_uid}/dim_broadcast")
def get_dim_broadcast(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Get the transmitter broadcast dimming level
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "GETDIMS"
        send(lora, cco_uid, cmd)
        res = receive(lora)
        (_, data) = decode(res, cmd)

        dimming_levels = [int(d) for d in data.split()]
        return Dimming(dimming_levels=dimming_levels)


@router.put("/{cco_uid}/dim_broadcast")
def dim_broadcast(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    dimming: Annotated[Dimming, Body(title="Three channel dimming level")],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Set the transmitter broadcast dimming level
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "SETDIMS"
        data = " ".join([str(d) for d in dimming.dimming_levels]).encode(
            encoding="ascii"
        )
        # Special case: separator between cmd and data is a single space " "
        temp = __encode__(cco_uid, cmd).rstrip()
        lora.write(temp + b"\x20" + data + b"\n")
        # No response from SETDIMS command


@router.get("/{cco_uid}/group/{sta_uid}")
def get_sta_group(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    sta_uid: Annotated[
        str, Path(title="Adapter serial number", min_length=12, max_length=12)
    ],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Get the group ID for a single adapter
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "SET_DEVICE_GROUP"
        # Data field includes the STA serial number, any group id and "00" for group read command
        data = sta_uid + "0" * 12 + "00"
        send(lora, cco_uid, cmd, data)

        # Group setting response takes two messages
        # The first response is just the STA uid
        res = receive(lora)

        cmd = "GROUPS"
        (_, data) = decode(res, cmd)

        if data != sta_uid:
            raise HTTPException(
                status_code=500, detail="STA UID response does not match"
            )

        # The second response includes both the uid and the group
        res = receive(lora)

        cmd = "SET_DEVICE_GROUP"
        (_, data) = decode(res, cmd)

        assert isinstance(data, str)
        if not data.startswith(sta_uid):
            raise HTTPException(
                status_code=500, detail="STA UID response does not match"
            )

        group = int(data[len(sta_uid) :])
        return {"group_id": group}


@router.put("/{cco_uid}/group/{sta_uid}")
def set_sta_group(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    sta_uid: Annotated[
        str, Path(title="Adapter serial number", min_length=12, max_length=12)
    ],
    group: Annotated[int, Query(title="Group ID", min=1, max=8)],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Set the group ID for a single adapter
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "SET_DEVICE_GROUP"
        data = sta_uid + str(group).zfill(12) + "01"
        send(lora, cco_uid, cmd, data)

        # Group setting response takes two messages
        # The first response is just the STA uid
        res = receive(lora)

        cmd = "GROUPS"
        (_, data) = decode(res, cmd)

        if data != sta_uid:
            raise HTTPException(
                status_code=500, detail="STA UID response does not match"
            )

        # The second response includes both the uid and the group
        res = receive(lora)

        cmd = "SET_DEVICE_GROUP"
        (_, data) = decode(res, cmd)

        assert isinstance(data, str)
        if not data.startswith(sta_uid):
            raise HTTPException(
                status_code=500, detail="STA UID response does not match"
            )

        group_res = int(data[len(sta_uid) :])

        if group != group_res:
            raise HTTPException(status_code=500, detail="STA group ID does not match")


@router.get("/{cco_uid}/groups")
def get_all_sta_groups(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Get the group ID for all STA
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "GETSTAGROUPS"
        send(lora, cco_uid, cmd)

        sta_uids = []
        group_ids = []
        # Continuously read until timeout, indicating end of response
        while (res := lora.readline()) != "":
            cmd = "GROUPS"
            try:
                (_, data) = decode(res, cmd)
            except HTTPException:
                # No STA groups
                return {"sta_uids": "", "group_ids": ""}

            assert isinstance(data, str)
            sta_uids.append(data)

            # Continue check each group
            res = receive(lora)

            cmd = "SET_DEVICE_GROUP"
            (_, data) = decode(res, cmd)
            assert isinstance(data, str)

            if not data.startswith(sta_uids[-1]):
                raise HTTPException(
                    status_code=500, detail="STA_UID response does not match"
                )

            group_id = int(data[len(sta_uids[-1]) :])
            group_ids.append(group_id)

        return {"sta_uids": sta_uids, "group_ids": group_ids}


@router.put("/{cco_uid}/dim_group")
def dim_group(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    group: Annotated[int, Query(title="Group ID", min=1, max=8)],
    dimming: Annotated[Dimming, Body(title="Three channel dimming level")] = Dimming(
        dimming_levels=[50, 50, 0]
    ),
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Enable group dimming for the given group ID
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "DIMALL3"
        # Data format: 5x 2 bytes of dimming levels, 1x 2 bytes of group ID, 1 byte of disable cmd
        data = b"".join(
            [d.to_bytes(2, byteorder="big") for d in dimming.dimming_levels]
        )
        # Last 2x dimming levels are not used
        data += 0x00.to_bytes(4, byteorder="big")
        data += group.to_bytes(2, byteorder="big") + 0x06.to_bytes(1, byteorder="big")
        send(lora, cco_uid, cmd, data)


@router.post("/disable_group_dimming/{cco_uid}")
def disable_group_dimming(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    group: Annotated[int, Query(title="Group ID", min=1, max=8)],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Disable group dimming for the given group ID
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "DIMALL3"
        # Data format: 5x 2 bytes of dimming levels, 1x 2 bytes of group ID, 1 byte of disable cmd
        data = (
            0x00.to_bytes(10, byteorder="big")
            + group.to_bytes(2, byteorder="big")
            + 0x07.to_bytes(1, byteorder="big")
        )
        send(lora, cco_uid, cmd, data)


@router.get("/{cco_uid}/tx_power")
def get_txpower(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Obtain the transmitting power setting
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "GetTxPower"
        send(lora, cco_uid, cmd)

        res = receive(lora)
        (_, data) = decode(res, cmd)

        assert isinstance(data, str)
        txpower = int(data)
        return {"txpower": txpower}


@router.put("/{cco_uid}/tx_power")
def set_txpower(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    txpower: Annotated[int, Query(title="Transmitting power", min=0, max=24)],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Set the transmitting power setting
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "SetTxPower"
        data = str(txpower)
        send(lora, cco_uid, cmd, data)

        res = receive(lora)
        (_, rx_data) = decode(res, cmd)

        if rx_data != data:
            raise HTTPException(
                status_code=500, detail="CCO TX power setting inconsistent"
            )


@router.put("/{cco_uid}/access_time")
def set_access_time(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    access_time: Annotated[
        int,
        Query(
            title="Time in minutes for searching adapters after commisioning",
            min=1,
            max=30,
        ),
    ],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Set the transmitter network discovery duration when autostarting
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "SetAccessTime"
        data = str(access_time)
        send(lora, cco_uid, cmd, data)

        res = receive(lora)
        (_, rx_data) = decode(res, cmd)

        if rx_data != data:
            raise HTTPException(
                status_code=500, detail="CCO access time setting inconsistent"
            )


@router.get("/{cco_uid}/access_time")
def get_access_time(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Get the transmitter network discovery duration when autostarting
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "GetAccessTime"
        send(lora, cco_uid, cmd)

        res = receive(lora)
        (_, rx_data) = decode(res, cmd)
        access_time = int(rx_data)

        return {"access_time": access_time}


@router.put("/{cco_uid}/band")
def set_frequency_band(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    band: Annotated[int, Query(title="Transmitter frequency band", min=0, max=3)],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Set the PLC communication frequency band
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "SetCCOBand"
        data = str(band)
        send(lora, cco_uid, cmd, data)

        res = receive(lora)
        (_, rx_data) = decode(res, cmd)

        if rx_data != data:
            raise HTTPException(
                status_code=500, detail="Transmitter band setting inconsistent"
            )


@router.get("/{cco_uid}/band")
def get_frequency_band(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Get the PLC communication frequency band
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "GetCCOBand"
        send(lora, cco_uid, cmd)

        res = receive(lora)
        (_, rx_data) = decode(res, cmd)
        band = int(rx_data)

        return {"band": band}


@router.put("/{cco_uid}/dim_channel")
def set_dimming_channel(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    channel_count: Annotated[
        int, Query(title="Transmitter dimming channel count", min=1, max=2)
    ],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Set the transmitter number of dimming channels for 0-10V analog input
    When set to 1 channel, the minimum output is 15% and 1st and 2nd channel are set to follow
    When set to 2 channel, the minimum output is 0% and 1st and 2nd channel are set to independent
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "SetCCOChannel"
        data = str(channel_count)
        send(lora, cco_uid, cmd, data)

        res = receive(lora)
        (_, rx_data) = decode(res, cmd)

        if rx_data != data:
            raise HTTPException(
                status_code=500,
                detail="Transmitter dimming channel setting inconsistent",
            )


@router.get("/{cco_uid}/dim_channel")
def get_dimming_channel(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Get the transmitter number of analog dimming channel
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "GetCCOChannel"
        send(lora, cco_uid, cmd)

        res = receive(lora)
        (_, rx_data) = decode(res, cmd)
        channel_count = int(rx_data)

        return {"channel_count": channel_count}


@router.get("/{cco_uid}/startup_control")
def get_startup_control(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Get the startup control setting for PLC adapters, ramp_up_duration is not used and meaningless
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "GetStartContral"
        send(lora, cco_uid, cmd)

        res = receive(lora)
        (_, rx_data) = decode(res, cmd)

        assert isinstance(rx_data, str)
        rx_list = rx_data.split(" ")
        is_enabled = rx_list[0] == "1"
        default_dimming = int(rx_list[1])
        _ = int(rx_list[2])

        startup_control = StartupControl(
            is_enabled=is_enabled,
            default_dimming=default_dimming,
        )

        return startup_control


@router.put("/{cco_uid}/startup_control")
def set_startup_control(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    startup_control: Annotated[
        StartupControl, Body(title="Adapter startup control setting")
    ],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Set the startup control setting for PLC adapters
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "SetStartContral"
        is_enabled = "1" if startup_control.is_enabled else "0"
        default_dimming = str(startup_control.default_dimming)
        # ramp_up_duration is meaningless but required in communication
        ramp_up_duration = "10"
        data = " ".join([is_enabled, default_dimming, ramp_up_duration])
        send(lora, cco_uid, cmd, data)

        res = receive(lora)
        (_, rx_data) = decode(res, cmd)

        if rx_data != data:
            raise HTTPException(
                status_code=500, detail="Startup control setting inconsistent"
            )


@router.put("/{cco_uid}/modbus_rtu_node_address")
def set_modbus_rtu_node_address(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    address: Annotated[int, Query(title="Modbus RTU node address", min=1, max=255)],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Set the modbus node address
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "SetModbusAddr"
        data = str(address)
        send(lora, cco_uid, cmd, data)

        res = receive(lora)
        (_, rx_data) = decode(res, cmd)

        if rx_data != data:
            raise HTTPException(
                status_code=500, detail="Modbus node address setting inconsistent"
            )


@router.get("/{cco_uid}/modbus_rtu_node_address")
def get_modbus_rtu_node_address(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Get the modbus node address setting
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "GetModbusAddr"
        send(lora, cco_uid, cmd)

        res = receive(lora)
        (_, rx_data) = decode(res, cmd)
        address = int(rx_data)

        return {"address": address}


@router.put("/{cco_uid}/ip_address")
def set_ip_address(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    ip_config: Annotated[IpConfig, Body(title="IP Address Setting")] = IpConfig(
        dynamic=False,
        address=IPv4Address("127.0.0.100"),
        netmask=IPv4Address("255.255.255.0"),
        gateway=IPv4Address("127.0.0.1"),
    ),
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Set the transmitter ethernet IP address
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "SetDeviceIP"
        if ip_config.dynamic:
            data = "0.0.0.0 0.0.0.0 0.0.0.0 0 0"
        else:
            # Format address netmask gateway separated by a single space, with a trailing 1 means static IP
            data = (
                " ".join(
                    [
                        str(ip_config.address),
                        str(ip_config.netmask),
                        str(ip_config.gateway),
                    ]
                )
                + " 1 "
            )

            # Checksum is the sum of numbers when using dot notation
            def ip_address_sum(addr: IPv4Address):
                return sum([int(a) for a in str(addr).split(".")])

            checksum = (
                ip_address_sum(ip_config.address)
                + ip_address_sum(ip_config.netmask)
                + ip_address_sum(ip_config.gateway)
            )
            checksum += 1

            data += str(checksum)

        send(lora, cco_uid, cmd, data)

        if ip_config.dynamic:
            # Response message is in 1 line
            res = receive(lora)
            (_, rx_data) = decode(res, cmd)

            if rx_data != "OK 0":
                raise HTTPException(
                    status_code=500, detail="Error setting dynamic IP address"
                )

        else:
            # Response message is in 4 lines
            # First line is the static IP address
            _ = receive(lora)
            _ = receive(lora)
            _ = receive(lora)
            res = receive(lora)
            (_, rx_data) = decode(res, cmd)

            if rx_data != "OK 1":
                raise HTTPException(
                    status_code=500, detail="Error setting static IP address"
                )


@router.get("/{cco_uid}/ip_address")
def get_ip_address(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Get the transmitter IP address setting
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "GetDeviceIP"
        send(lora, cco_uid, cmd)

        res = receive(lora)
        (_, rx_data) = decode(res, cmd)
        assert isinstance(rx_data, str)
        fields = rx_data.split(" ")
        ip_addr = IpConfig(
            dynamic=False,
            address=IPv4Address(fields[0]),
            netmask=IPv4Address(fields[1]),
            gateway=IPv4Address(fields[2]),
        )

        return ip_addr


@router.delete("/{cco_uid}/whitelist")
def clear_whitelist(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Remove the PLC communication STA whitelist
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "WHCLR"
        send(lora, cco_uid, cmd)

        # Response does not have data field
        _ = receive(lora)
        # Transmitter PLC module will reload whitelist so wait here
        # TODO: wait until PLC module is reloaded


@router.get("/{cco_uid}/whitelist")
def get_whitelist(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Get the PLC communication STA whitelist
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "WHSGET"
        send(lora, cco_uid, cmd)

        sta_list = []

        while True:
            res = receive(lora)
            cmd = "WHMULT"
            (_, data) = decode(res, cmd)
            fields = data.split()

            # 0th field is starting index,
            index = int(fields[0])
            # 1st field is number of sta address in this message
            length = int(fields[1])
            # 2rd field is total number of sta address
            total = int(fields[2])

            # The rest are sta address
            sta_list.extend(fields[3:])

            if index + length == total:
                break

    return {"whitelist": sta_list}


@router.post("/{cco_uid}/whitelist")
def set_whitelist(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    sta_list: Annotated[list[str], Body(title="List of STA UIDs")],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Set the PLC communication STA whitelist
    """
    clear_whitelist(cco_uid, timeout)
    with Serial(portname, timeout=timeout) as lora:
        cmd = "WHSTART"
        send(lora, cco_uid, cmd)

        res = receive(lora)
        (_, _) = decode(res, cmd)

        # Send 4 STA UIDs at a time
        index = 0
        stop_flag = False

        while True:
            length = 4
            total = len(sta_list)
            fields = [str(index), str(length), str(total)]

            if index + 4 > total:
                stop_flag = True
                fields.extend(sta_list[index:])
            else:
                fields.extend(sta_list[index : index + 4])

            cmd = "WHMLIST"
            data = " ".join(fields)
            send(lora, cco_uid, cmd, data)

            res = receive(lora)
            (_, res_data) = decode(res, cmd)
            assert isinstance(res_data, str)

            if data.startswith(res_data):
                index += 4
            else:
                cmd = "WHEND"
                send(lora, cco_uid, cmd)
                raise HTTPException(
                    status_code=500, detail="Unknown failure in setting whitelist"
                )

            if stop_flag:
                break

        cmd = "WHEND"
        send(lora, cco_uid, cmd)


@router.post("/{cco_uid}/reboot")
def reboot(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port read timeout in seconds")
    ] = 0.5,
):
    """
    Force the transmitter to power cycle
    """
    with Serial(portname, timeout=timeout) as lora:
        cmd = "REBOOTCCO"
        send(lora, cco_uid, cmd)


@router.websocket("/{cco_uid}/network_discovery")
async def rebuild(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    websocket: WebSocket,
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port timeout in seconds")
    ] = 0.5,
):
    """
    Force the transmitter to rebuild its whitelist
    """
    lora = Serial(portname, timeout=timeout)

    await websocket.accept()

    async def start():
        cmd = "REBOOTCCO"
        send(lora, cco_uid, cmd)
        print("Rebooting")

        await asyncio.sleep(10)

        cmd = "SETTINGSTART"
        send(lora, cco_uid, cmd)
        print("Researching")

    async def streaming():
        while True:
            res = lora.readlines()

            if res:
                await websocket.send_text(str(res))

            try:
                ws_res = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                if ws_res == "STOP":
                    stop_cmd = "WHITESTOP"
                    send(lora, cco_uid, stop_cmd)
            except TimeoutError:
                pass

    async with asyncio.TaskGroup() as tg:
        _ = tg.create_task(start())
        _ = tg.create_task(streaming())

    # Wait until the searching is completely stopped
    await asyncio.sleep(3)

    # Return the last few messages to client
    res = lora.readlines()
    if res:
        await websocket.send_text(str(res))


@router.get("/{cco_uid}/status/{sta_uid}")
def get_status(
    cco_uid: Annotated[
        str, Path(title="Transmitter serial number", min_length=8, max_length=8)
    ],
    sta_uid: Annotated[
        str, Path(title="Adapter serial number", min_length=12, max_length=12)
    ],
    timeout: Annotated[
        float, Query(min=0.1, title="Serial port timeout in seconds")
    ] = 0.5,
):
    """Retrieve the adapter status"""
    with Serial(portname, timeout=timeout) as lora:
        cmd = "STATUS"
        data = sta_uid
        send(lora, cco_uid, cmd, data)
        res = receive(lora)
        (_, res_data) = decode(res, cmd)

        if res_data != data:
            raise HTTPException(
                status_code=500, detail="Inconsistent STA UID in response"
            )

        res = receive(lora)
        (_, res_data) = decode(res, "STA")
        assert isinstance(res_data, str)

        # Response data starts with STA UID
        if not res_data.startswith(sta_uid):
            raise HTTPException(
                status_code=500, detail="Inconsistent STA UID in response"
            )
        # Then firmware version code of STA
        index = len(sta_uid)
        length = 6
        firmware_version = res_data[index : index + length]

        # Then the dimming levels
        index += length
        length = 6

        dimming_level_0 = int(bytes.fromhex(res_data[index + 1] + res_data[index]))
        dimming_level_1 = int(bytes.fromhex(res_data[index + 3] + res_data[index + 2]))
        dimming_level_2 = int(bytes.fromhex(res_data[index + 5] + res_data[index + 4]))

        dimming = Dimming(
            dimming_levels=[dimming_level_0, dimming_level_1, dimming_level_2]
        )

        # Then the dimming control mode:
        # 00 broadcast
        # 04 single dimming enable
        # 05 single dimming disable
        # 06 group dimming enable
        # 07 group dimming disable
        index += length
        length = 1

        if res_data[index] == "00":
            dimming_mode = "broadcast"
        elif res_data[index] == "04":
            dimming_mode = "single enable"
        elif res_data[index] == "05":
            dimming_mode = "single disable"
        elif res_data[index] == "06":
            dimming_mode = "group enable"
        elif res_data[index] == "07":
            dimming_mode = "group disable"
        else:
            dimming_mode = "unknown " + res_data[index]

        index += length

        # Power meter data starts with 0x55
