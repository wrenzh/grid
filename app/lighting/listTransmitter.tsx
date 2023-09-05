import { Suspense, useState } from "react";
import { IoRefreshSharp } from "react-icons/io5";
import Separator from "./separator";

export default function ListTransmitter({
    updateTransmitterUid,
}: {
    updateTransmitterUid: Function;
}) {
    interface TransmitterAddress {
        address: string;
    }

    const [transmitterUidItem, setTransmitterUidItem] = useState("")

    async function fetchData() {
        try {
            const response = await fetch("/api/lighting/list_cco");
            if (response.ok) {
                const json: TransmitterAddress = await response.json();
                setTransmitterUidItem(json.address);
            } else {
              setTransmitterUidItem("ERROR");
            }
        } catch (e) {
            console.error(e);
        }
    }

    async function TransmitterUid() {
        await fetchData();
        return (
            <>
                <div className="flex flex-row justify-center">
                    <select
                        className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 w-80 p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
                        size={1}
                        onChange={(e) =>
                            updateTransmitterUid(e.target.value)
                        }
                    >
                        <option value={transmitterUidItem} key={transmitterUidItem}>
                            {transmitterUidItem}
                        </option>
                    </select>
                    <IoRefreshSharp
                        size={40}
                        title={"Force rescan the transmitter ID"}
                        onClick={() => fetchData()}
                        className="p-2"
                    />
                </div>
            </>
        );
    }

    return (
        <>
            <label className="flex justify-center mb-2 text-lg font-medium text-gray-900 dark:text-white">
                Select a transmitter ID to start
            </label>
            <Suspense fallback={<option value="">Loading...</option>}>
                <TransmitterUid />
            </Suspense>
            <Separator />
        </>
    );
}
