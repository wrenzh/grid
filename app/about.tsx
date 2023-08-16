import Img from "next/image";
import Link from "next/link";
import NFF from "../public/NFF.jpg";
import Navbar from "@/components/navbar";

export default function About() {
  return (
    <>
      <Navbar selectedTab={"About"} />
      <Img src={NFF} alt="Natural Fresh Farms" />
      <Link
        className="flex justify-center items-center"
        href="mailto:wzhang@hawthornegc.com"
      >
        Contact: Wen Zhang (wzhang@hawthornegc.com)
      </Link>
    </>
  );
}
