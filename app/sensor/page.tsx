"use client"

import Sensor from "./sensor"
import Navbar from "@/components/navbar";

export default function Page() {
    return (
        <>
            <Navbar selectedTab={"Sensor"} />
            <Sensor />
        </>
    );
}
