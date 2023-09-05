"use client";

import { useState } from "react";
import Navbar from "@/components/navbar";
import ListTransmitter from "@/app/lighting/listTransmitter";
import ControlModes from "@/app/lighting/controlModes";

export function Lighting() {
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

export default function Page() {
    return <Lighting />
}