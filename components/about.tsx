import Img from "next/image";
import Link from "next/link";
import NFF from "../public/NFF.jpg";

export default function About() {
  return (
    <>
      <Img src={NFF} alt="Natural Fresh Farms" />
      <Link className="flex justify-center items-center" href="mailto:wzhang@hawthornegc.com">
        Contact: Wen Zhang (wzhang@hawthornegc.com)
      </Link>
    </>
  );
}
