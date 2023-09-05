"use client"

import { useState, Suspense, useEffect } from "react";
import { RxReset } from "react-icons/rx";
import Separator from "./separator";

export default function ControlModes({
    transmitterUid
}: {
    transmitterUid: string
}) {
    const [analogEnabled, setAnalogEnabled] = useState(true);
    const [buttonEnabled, setButtonEnabled] = useState(true);
    const [modbusEnabled, setModbusEnabled] = useState(true);
    const [bacnetEnabled, setBacnetEnabled] = useState(true);
    const [debugEnabled, setDebugEnabled] = useState(true);

    interface TransmitterControlModeInterface {
        analog: boolean;
        button: boolean;
        modbus: boolean;
        bacnet: boolean;
        debug: boolean;
    }

    async function fetchData() {
        const response = await fetch(
            "/api/lighting/" + transmitterUid + "/control_mode"
        );
        const json: TransmitterControlModeInterface = await response.json();
        setAnalogEnabled(json.analog);
        setButtonEnabled(json.button);
        setModbusEnabled(json.modbus);
        setBacnetEnabled(json.bacnet);
        setDebugEnabled(json.debug);
    } 


    useEffect(() => {
        async function updateData() {
            if (transmitterUid != "ERROR" && transmitterUid != "") {
                return;
            }
            const data = {
                analog: analogEnabled,
                button: buttonEnabled,
                modbus: modbusEnabled,
                bacnet: bacnetEnabled,
                debug: debugEnabled,
            };
            const _ = await fetch(
                "/api/lighting/" + transmitterUid + "/control_mode",
                {
                    method: "PUT",
                    body: JSON.stringify(data),
                }
            );
        }
        updateData()
    }, [analogEnabled, buttonEnabled, modbusEnabled, bacnetEnabled, debugEnabled, transmitterUid]);

    async function TransmitterControlMode() {
        if (transmitterUid != "ERROR" && transmitterUid != "") {
            await fetchData();
        }
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
        const _ = await fetch("/api/lighting/" + transmitterUid + "/reset_control_mode", { method: "POST"});
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
