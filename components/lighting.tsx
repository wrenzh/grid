import { useState, Suspense } from "react";
import { IoRefresh } from "react-icons/io5";

const server_url = "localhost:8080";

function ListTransmitter({
  transmitterUid,
  updateTransmitterUid,
}: {
  transmitterUid: string;
  updateTransmitterUid: Function;
}) {
  interface TransmitterAddress {
    address: string;
  }

  async function fetchData() {
    try {
      const response = await fetch(server_url + "/list_cco");
      const json = await response.json();
      const address: TransmitterAddress = JSON.parse(json);
      updateTransmitterUid(address.address);
    } catch (e) {
      console.error(e);
      updateTransmitterUid("ERROR");
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
          >
            <option value={transmitterUid}>{transmitterUid}</option>
          </select>
          <button
            onClick={() => fetchData()}
            title={"Force rescan the transmitter ID"}
          >
            <IoRefresh />
          </button>
        </div>
      </>
    );
  }

  return (
    <>
      <label className="flex justify-center mb-2 text-sm font-medium text-gray-900 dark:text-white">Select a transmitter ID to start</label>
      <Suspense fallback={<option value="">Loading...</option>}>
        <TransmitterUid />
      </Suspense>
    </>
  );
}

function ControlModes({ transmitterUid }: { transmitterUid: string }) {
  const [analogEnabled, setAnalogEnabled] = useState(true);
  const [buttonEnabled, setButtonEnabled] = useState(true);
  const [modbusEnabled, setModbusEnabled] = useState(true);
  const [bacnetEnabled, setBacnetEnabled] = useState(true);
  const [debugEnabled, setDebugEnabled] = useState(true);

  interface TransmitterControlModeInterface {
    analog : boolean;
    button : boolean;
    modbus : boolean;
    bacnet : boolean;
    debug : boolean;
  }

  async function fetchData() {
    try {
      const response = await fetch(server_url + "/list_cco");
      const json = await response.json();
      const controlMode : TransmitterControlModeInterface = JSON.parse(json);
      setAnalogEnabled(controlMode.analog);
      setButtonEnabled(controlMode.button);
      setModbusEnabled(controlMode.modbus);
      setBacnetEnabled(controlMode.bacnet);
      setDebugEnabled(controlMode.debug);
    } catch (e) {
      console.error(e);
    }
  }

  async function TransmitterControlMode() {
    await fetchData();
    return (
      <>
        <input type="checkbox" checked={analogEnabled}></input>
        <label>Analog 0-10V</label>
        <input type="checkbox" checked={buttonEnabled} disabled={true}></input>
        <label>Button</label>
        <input type="checkbox" checked={modbusEnabled}></input>
        <label>Modbus RTU</label>
        <input type="checkbox" checked={bacnetEnabled}></input>
        <label>BacNet/IP</label>
        <input type="checkbox" checked={debugEnabled}></input>
        <label>RS232 Debug</label>
      </>
    );
  }

  return (
    <>
    <label>Transmitter control modes</label>
    <Suspense fallback={<label>Loading...</label>}>
      <TransmitterControlMode />
    </Suspense>
    </>
  )

};

function Separator() {
  return <hr className="w-96 h-1 mx-auto my-2 bg-gray-100 border-0 rounded md:my-10 dark:bg-gray-700"></hr>;
}

export default function Lighting() {
  const [transmitterUid, setTransmitterUid] = useState("");
  return (
    <>
      <Separator />
      <ListTransmitter
        transmitterUid={transmitterUid}
        updateTransmitterUid={(a: string) => setTransmitterUid(a)}
      />
      <Separator />
      <ControlModes transmitterUid={transmitterUid}/>
    </>
  );
}
