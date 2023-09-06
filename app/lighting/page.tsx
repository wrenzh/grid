"use client";

import { useState } from "react";
import Navbar from "@/components/navbar";
import ListTransmitter from "@/app/lighting/listTransmitter";
import ControlModes from "@/app/lighting/controlModes";
import BroadcastDimming from "./broadcastDimming";

export function Lighting() {
  const [transmitterUid, setTransmitterUid] = useState("");
  return (
      <>
          <Navbar selectedTab={"Lighting"} />
          <ListTransmitter
              transmitterUid={transmitterUid}
              setTransmitterUid={setTransmitterUid}
          />
          <ControlModes transmitterUid={transmitterUid} />
          <BroadcastDimming transmitterUid={transmitterUid} />
      </>
  );
}

export default function Page() {
    return <Lighting />
}