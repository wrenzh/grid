import Navbar from "@/components/navbar";

function Sensor() {
    return (
        <>
            <Navbar selectedTab={"Sensor"} />
            <p>Hold your breath... It is coming!</p>
        </>
    );
}

export default function Page() {
    return <Sensor />;
}
