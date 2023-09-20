import { useEffect, useState } from "react";
import { SiOxygen, SiLeaflet, SiRoots } from "react-icons/si";
import { IoWater } from "react-icons/io5";
import { FaTemperatureHigh } from "react-icons/fa6";
import { GiAcid } from "react-icons/gi";
import { SlRefresh } from "react-icons/sl";

function SensorIcon({ sensorType }: { sensorType: number }) {
  if (sensorType === 100 || sensorType === 101 || sensorType === 102)
    return <SiLeaflet />;
  if (sensorType === 103) return <SiRoots />;
  if (sensorType === 150) return <IoWater />;
  if (sensorType === 200) return <FaTemperatureHigh />;
  if (sensorType === 300) return <SiOxygen />;
  if (sensorType === 400) return <GiAcid />;
}

export default function Sensor() {
  const [sensorNames, setSensorNames] = useState([""]);
  const [sensorTypes, setSensorTypes] = useState([0]);
  const [measurements, setMeasurements] = useState([""]);

  interface SensorNames {
    sensor_names: Array<string>;
  }

  interface SingleMeasurement {
    result: string;
  }

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch("/api/sensor/names");
        const json: SensorNames = await response.json();
        setSensorNames(json.sensor_names);
      } catch (e) {
        console.log(e);
      }
    };
    fetchData();
  });

  const get_measurement = async (id: number) => {
    try {
      const response = await fetch("/api/sensor/single_measurement?id=" + id);
      const json: SingleMeasurement = await response.json();
      setMeasurements([]);
    } catch (e) {
      console.log(e);
    }
  };

  return (
    <>
      <div className="flex flex-row justify-center">
        <ul>
          {sensorNames.map((n: string, i: number) => (
            <li
              key={n}
              className="mb-2 text-lg font-medium text-gray-900 dark:text-white"
            >
              <div className="flex flex-column">
                <SensorIcon sensorType={sensorTypes[i]} />
                <p>{n}</p>
                <p>{measurements[i]}</p>
                <button onClick={() => get_measurement(i)}>
                  <SlRefresh />
                </button>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </>
  );
}
