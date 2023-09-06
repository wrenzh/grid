import { useState, useEffect } from "react";
import Separator from "./separator";

export default function ControlModes({
    transmitterUid,
}: {
    transmitterUid: string;
}) {
    const [analogEnabled, setAnalogEnabled] = useState(true);
    const [buttonEnabled, setButtonEnabled] = useState(true);
    const [modbusEnabled, setModbusEnabled] = useState(true);
    const [bacnetEnabled, setBacnetEnabled] = useState(true);
    const [debugEnabled, setDebugEnabled] = useState(true);
    const [loading, setLoading] = useState(true);

    interface TransmitterControlModeInterface {
        analog: boolean;
        button: boolean;
        modbus: boolean;
        bacnet: boolean;
        debug: boolean;
    }

    async function setData(control_mode: TransmitterControlModeInterface) {
        if (transmitterUid == "ERROR" || transmitterUid == "") {
            return;
        }
        setLoading(true);
        const data = control_mode;
        const _ = await fetch(
            "/api/lighting/" + transmitterUid + "/control_mode",
            {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            }
        );
        setLoading(false);
    }

    async function updateData() {
        if (transmitterUid == "ERROR" || transmitterUid == "") {
            return;
        }
        const response = await fetch(
            "/api/lighting/" + transmitterUid + "/control_mode"
        );
        const json: TransmitterControlModeInterface = await response.json();
        setAnalogEnabled(json.analog);
        setButtonEnabled(json.button);
        setModbusEnabled(json.modbus);
        setBacnetEnabled(json.bacnet);
        setDebugEnabled(json.debug);
        setLoading(false);
    }

    useEffect(() => {
        async function fetchData() {
            if (transmitterUid == "ERROR" || transmitterUid == "") {
                return;
            }
            const response = await fetch(
                "/api/lighting/" + transmitterUid + "/control_mode"
            );
            const json: TransmitterControlModeInterface = await response.json();
            setAnalogEnabled(json.analog);
            setButtonEnabled(json.button);
            setModbusEnabled(json.modbus);
            setBacnetEnabled(json.bacnet);
            setDebugEnabled(json.debug);
            setLoading(false);
        }
        fetchData();
    }, [transmitterUid]);

    function TransmitterControlMode() {
        return (
            <>
                <div className="flex justify-center">
                    <div className="grid grid-cols-3 gap-x-4 auto-cols-auto">
                        <div className="flex-1">
                            <input
                                type="checkbox"
                                checked={analogEnabled}
                                disabled={loading}
                                onChange={() => {
                                    setAnalogEnabled(!analogEnabled);
                                    setData({
                                        analog: !analogEnabled,
                                        button: buttonEnabled,
                                        modbus: modbusEnabled,
                                        bacnet: bacnetEnabled,
                                        debug: debugEnabled,
                                    });
                                }}
                            ></input>
                            <label className="p-2">Analog 0-10V</label>
                        </div>
                        <div className="flex-1">
                            <input
                                type="checkbox"
                                checked={buttonEnabled}
                                disabled={true}
                            ></input>
                            <label className="p-2">Button</label>
                        </div>
                        <div className="flex-1">
                            <input
                                type="checkbox"
                                checked={modbusEnabled}
                                disabled={loading}
                                onChange={() => {
                                    setModbusEnabled(!modbusEnabled);
                                    setData({
                                        analog: analogEnabled,
                                        button: buttonEnabled,
                                        modbus: !modbusEnabled,
                                        bacnet: bacnetEnabled,
                                        debug: debugEnabled,
                                    });
                                }}
                            ></input>
                            <label className="p-2">Modbus RTU</label>
                        </div>
                        <div className="flex-1">
                            <input
                                type="checkbox"
                                checked={bacnetEnabled}
                                disabled={loading}
                                onChange={() => {
                                    setBacnetEnabled(!bacnetEnabled);
                                    setData({
                                        analog: analogEnabled,
                                        button: buttonEnabled,
                                        modbus: modbusEnabled,
                                        bacnet: !bacnetEnabled,
                                        debug: debugEnabled,
                                    });
                                }}
                            ></input>
                            <label className="p-2">BacNet/IP</label>
                        </div>
                        <div className="flex-1">
                            <input
                                type="checkbox"
                                checked={debugEnabled}
                                disabled={loading}
                                onChange={() => {
                                    setDebugEnabled(!debugEnabled);
                                    setData({
                                        analog: analogEnabled,
                                        button: buttonEnabled,
                                        modbus: modbusEnabled,
                                        bacnet: bacnetEnabled,
                                        debug: !debugEnabled,
                                    });
                                }}
                            ></input>
                            <label className="p-2">RS232 Debug</label>
                        </div>
                    </div>
                </div>
            </>
        );
    }

    async function reset() {
        if (transmitterUid == "ERROR" || transmitterUid == "") {
            return;
        }
        try {
            const _ = await fetch(
                "/api/lighting/" + transmitterUid + "/reset_control_mode",
                { method: "POST" }
            );
        } catch (e) {
            console.log(e);
        }
        updateData();
    }

    return (
        <>
            <div className="flex flex-row justify-center items-baseline">
                <label className="flex justify-center mb-2 text-lg font-medium text-gray-900 dark:text-white">
                    Transmitter control modes
                </label>
            </div>
            <TransmitterControlMode />
            <div className="flex flex-row pt-4 justify-center">
                <button
                    className="w-40 bg-transparent hover:bg-blue-500 text-blue-700 font-semibold hover:text-white py-2 px-4 border border-blue-500 hover:border-transparent rounded"
                    title="Reset transmitter control mode"
                    onClick={() => {
                        setLoading(true);
                        reset();
                    }}
                >
                    Reset
                </button>
            </div>
            <Separator />
        </>
    );
}
