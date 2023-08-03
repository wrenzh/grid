"use client";

import React, { useState } from "react"
import Navbar from "../components/navbar"
import Lighting from "../components/lighting"
import Sensor from "../components/sensor"
import About from "../components/about"

export default function Home() {
  const [selectedTab, setSelectedTab] = useState(0);

  const tabs = [
    { name: "Lighting", link: <Lighting /> },
    { name: "Sensor", link: <Sensor /> },
    { name: "About", link: <About /> },
  ];

  const handleClick = (index: number) => {
    setSelectedTab(index);
  }

  return (
    <main>
      <Navbar tabs={tabs} selectedTab={selectedTab} handleClick={handleClick}/>
      {tabs[selectedTab].link}
    </main>
  );
}
