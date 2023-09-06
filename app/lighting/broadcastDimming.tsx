import { useEffect, useState } from "react";
import Separator from "./separator";

export default function BroadcastDimming({
    transmitterUid,
}: {
    transmitterUid: string;
}) {
    const [dimming, setDimming] = useState([0, 0, 0]);
    const [loading, setLoading] = useState(true);

    interface Dimming {
        dimming_levels: Array<number>;
    }

    useEffect(() => {
        if (loading) {
            return;
        }
        const setData = async (dimming: Array<number>) => {
            if (transmitterUid == "ERROR" || transmitterUid == "") {
                return;
            }
            try {
                const data = {
                    dimming_levels: dimming,
                };
                const _ = await fetch(
                    "/api/lighting/" + transmitterUid + "/dim_broadcast",
                    {
                        method: "PUT",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify(data),
                    }
                );
            } catch (e) {
                console.log(e);
            }
        };

        setData(dimming);
    });

    useEffect(() => {
        const fetchData = async () => {
            if (transmitterUid == "ERROR" || transmitterUid == "") {
                return;
            }
            try {
                const response = await fetch(
                    "/api/lighting/" + transmitterUid + "/dim_broadcast"
                );
                const json: Dimming = await response.json();
                setDimming(json.dimming_levels);
                setLoading(false);
            } catch (e) {
                console.log(e);
            }
        };
        fetchData();
    }, [transmitterUid]);

    return (
        <>
            <div className="flex flex-col jusity-center items-center">
                <label className="flex justify-center mb-2 text-lg font-medium text-gray-900 dark:text-white">
                    Broadcast Dimming
                </label>
                <div className="flex flex-row jusity-center items-center p-2">
                    <label className="pr-4">Channel 1</label>
                    <input
                        type="range"
                        min="0"
                        max="100"
                        step="0.1"
                        value={dimming[0] / 10}
                        disabled={loading}
                        onChange={(e) => {
                            e.preventDefault();
                            const temp = [
                                Number(e.target.value) * 10,
                                dimming[1],
                                dimming[2],
                            ];
                            setDimming(temp);
                        }}
                        className="w-60 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                    />
                    <span className="w-16 text-center text-xs font-semibold inline-block py-1 px-2 rounded text-sky-600 bg-sky-200 uppercase last:mr-0 mr-1">
                        {(dimming[0] / 10).toFixed(1)}
                    </span>
                </div>
                <div className="flex flex-row jusity-center items-center p-2">
                    <label className="pr-4">Channel 2</label>
                    <input
                        type="range"
                        min="0"
                        max="100"
                        step="0.1"
                        value={dimming[1] / 10}
                        disabled={loading}
                        onChange={(e) => {
                            e.preventDefault();
                            const temp = [
                                dimming[0],
                                Number(e.target.value) * 10,
                                dimming[2],
                            ];
                            setDimming(temp);
                        }}
                        className="w-60 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                    />
                    <span className="w-16 text-center text-xs font-semibold inline-block py-1 px-2 rounded text-fuchsia-600 bg-fuchsia-200 uppercase last:mr-0 mr-1">
                        {(dimming[1] / 10).toFixed(1)}
                    </span>
                </div>
                <div className="flex flex-row justify-center items-center p-2">
                    <label className="pr-4">Channel 3</label>
                    <input
                        type="range"
                        min="0"
                        max="100"
                        step="0.1"
                        value={dimming[2] / 10}
                        disabled={loading}
                        onChange={(e) => {
                            e.preventDefault();
                            const temp = [
                                dimming[0],
                                dimming[1],
                                Number(e.target.value) * 10,
                            ];
                            setDimming(temp);
                        }}
                        className="w-60 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                    />
                    <span className="w-16 text-center text-xs font-semibold inline-block py-1 px-2 rounded text-lime-600 bg-lime-200 uppercase last:mr-0 mr-1">
                        {(dimming[2] / 10).toFixed(1)}
                    </span>
                </div>
            </div>
            <Separator />
        </>
    );
}
