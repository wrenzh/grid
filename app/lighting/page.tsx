"use client";

import { useState } from "react";
import Navbar from "@/components/navbar";
import ListTransmitter from "@/app/lighting/listTransmitter";
import ControlModes from "@/app/lighting/controlModes";

export function Lighting() {
  const [transmitterUid, setTransmitterUid] = useState("");
  return (
    <>
      <Navbar selectedTab={"Lighting"} />
      <ListTransmitter
        updateTransmitterUid={(a: string) => setTransmitterUid(a)}
      />
      <ControlModes transmitterUid={transmitterUid}/>
    </>
  );
}

export default function Page() {
    return <Lighting />
}