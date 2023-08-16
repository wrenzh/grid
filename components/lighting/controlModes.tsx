import { useState, Suspense } from "react";
import { RxReset } from "react-icons/rx";
import Separator from "./separator";

export default function ControlModes({
    transmitterUid,
    serverUrl,
}: {
    transmitterUid: string;
    serverUrl: string;
}) {
    const [analogEnabled, setAnalogEnabled] = useState(true);
    const [buttonEnabled, setButtonEnabled] = useState(true);
    const [modbusEnabled, setModbusEnabled] = useState(true);
    const [bacnetEnabled, setBacnetEnabled] = useState(true);
    const [debugEnabled, setDebugEnabled] = useState(true);
    const [changed, setChanged] = useState(false);

    interface TransmitterControlModeInterface {
        analog: boolean;
        button: boolean;
        modbus: boolean;
        bacnet: boolean;
        debug: boolean;
    }

    async function fetchData() {
        try {
            if (!changed) {
                const response = await fetch(
                    serverUrl + "/" + transmitterUid + "/control_mode"
                );
                const json = await response.json();
                const controlMode: TransmitterControlModeInterface =
                    JSON.parse(json);
                setAnalogEnabled(controlMode.analog);
                setButtonEnabled(controlMode.button);
                setModbusEnabled(controlMode.modbus);
                setBacnetEnabled(controlMode.bacnet);
                setDebugEnabled(controlMode.debug);
            } else {
                const data = {
                    analog: analogEnabled,
                    button: buttonEnabled,
                    modbus: modbusEnabled,
                    bacnet: bacnetEnabled,
                    debug: debugEnabled,
                };
                const response = await fetch(
                    "http://" +
                        serverUrl +
                        "/" +
                        transmitterUid +
                        "/control_mode",
                    {
                        method: "PUT",
                        body: JSON.stringify(data),
                    }
                );
                if (!response.ok) {
                } else {
                    setChanged(false);
                }
            }
        } catch (e) {
            console.error(e);
        }
    }

    async function TransmitterControlMode() {
        // await fetchData();
        return (
            <>
                <div className="flex justify-center">
                    <div className="grid grid-cols-3 gap-x-4 auto-cols-auto">
                        <div className="flex-1">
                            <input
                                type="checkbox"
                                checked={analogEnabled}
                                onChange={() => {
                                    setAnalogEnabled(!analogEnabled);
                                    setChanged(true);
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
                                onChange={() => {
                                    setModbusEnabled(!modbusEnabled);
                                    setChanged(true);
                                }}
                            ></input>
                            <label className="p-2">Modbus RTU</label>
                        </div>
                        <div className="flex-1">
                            <input
                                type="checkbox"
                                checked={bacnetEnabled}
                                onChange={() => {
                                    setBacnetEnabled(!bacnetEnabled);
                                    setChanged(true);
                                }}
                            ></input>
                            <label className="p-2">BacNet/IP</label>
                        </div>
                        <div className="flex-1">
                            <input
                                type="checkbox"
                                checked={debugEnabled}
                                onChange={() => {
                                    setDebugEnabled(!debugEnabled);
                                    setChanged(true);
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
        const request = await fetch(
            serverUrl + "/" + transmitterUid + "/control_mode",
            {
                method: "DELETE",
            }
        );
    }

    return (
        <>
            <div className="flex flex-row justify-center items-baseline">
                <label className="flex justify-center mb-2 text-lg font-medium text-gray-900 dark:text-white">
                    Transmitter control modes
                </label>
                <RxReset
                    size={12}
                    title={"Reset the transmitter control mode"}
                    onClick={() => reset()}
                />
            </div>
            <Suspense fallback={<label>Loading...</label>}>
                <TransmitterControlMode />
            </Suspense>
            <Separator />
        </>
    );
}
