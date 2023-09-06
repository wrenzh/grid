"use client";

import { useState, useEffect } from "react";
import { IoRefreshSharp } from "react-icons/io5";
import Separator from "./separator";

function TransmitterUid({
    transmitterUid,
    setTransmitterUid,
}: {
    transmitterUid: string;
    setTransmitterUid: Function;
}) {
    const [loading, setLoading] = useState(true);

    async function updateTransmitterUid() {
        try {
            const response = await fetch("/api/lighting/list_cco");
            const json = await response.json();
            setTransmitterUid(json.address);
        } catch (e) {
            setTransmitterUid("ERROR");
        }
        setLoading(false);
    }
    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch("/api/lighting/list_cco");
                const json = await response.json();
                setTransmitterUid(json.address);
            } catch (e) {
                setTransmitterUid("ERROR");
            }
            setLoading(false);
        };

        fetchData();
    }, [setTransmitterUid]);

    return (
        <div className="flex flex-row justify-center">
            {loading ? (
                <>
                    <button className="w-40 bg-transparent hover:bg-blue-500 text-blue-700 font-semibold hover:text-white py-2 px-4 border border-blue-500 hover:border-transparent rounded">
                        Loading...
                    </button>
                    <IoRefreshSharp
                        size={40}
                        title={"Force rescan the transmitter ID"}
                        className="p-2"
                    />
                </>
            ) : (
                <>
                    <button className="w-40 bg-transparent hover:bg-blue-500 text-blue-700 font-semibold hover:text-white py-2 px-4 border border-blue-500 hover:border-transparent rounded">
                        {transmitterUid}
                    </button>
                    <IoRefreshSharp
                        size={40}
                        title={"Force rescan the transmitter ID"}
                        onClick={() => {
                            setLoading(true);
                            updateTransmitterUid();
                        }}
                        className="p-2"
                    />
                </>
            )}
        </div>
    );
}

export default function ListTransmitter({
    transmitterUid,
    setTransmitterUid,
}: {
    transmitterUid: string;
    setTransmitterUid: Function;
}) {
    return (
        <>
            <label className="flex justify-center mb-2 text-lg font-medium text-gray-900 dark:text-white">
                Select transmitter UID to start
            </label>
            <TransmitterUid
                transmitterUid={transmitterUid}
                setTransmitterUid={setTransmitterUid}
            />
            <Separator />
        </>
    );
}
