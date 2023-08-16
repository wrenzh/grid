"use client";

import { useState } from "react";
import Navbar from "@/components/navbar";
import ListTransmitter from "@/components/lighting/listTransmitter";
import ControlModes from "@/components/lighting/controlModes";

export default function Lighting() {
  const serverUrl = "/api/lighting";
  const [transmitterUid, setTransmitterUid] = useState("");
  return (
    <>
      <Navbar selectedTab={"Lighting"} />
      <ListTransmitter
        transmitterUid={transmitterUid}
        updateTransmitterUid={(a: string) => setTransmitterUid(a)}
        serverUrl={serverUrl}
      />
      <ControlModes transmitterUid={transmitterUid} serverUrl={serverUrl} />
    </>
  );
}
