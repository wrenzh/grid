import Img from "next/image";
import Link from "next/link";
import agroluxLogo from "../public/agrolux.png";
import React from "react";

type TabType = {
  name: string;
  link: React.JSX.Element;
};

export default function Navbar({
  tabs,
  selectedTab = 0,
  handleClick,
}: {
  tabs: TabType[];
  selectedTab: number;
  handleClick: Function;
}) {
  const tabStyle = (index: number) => {
    return index == selectedTab
      ? "block py-2 pl-3 pr-4 text-white bg-blue-700 rounded md:bg-transparent md:text-blue-700 md:p-0 dark:text-white md:dark:text-blue-500"
      : "block py-2 pl-3 pr-4 text-gray-900 rounded hover:bg-gray-100 md:hover:bg-transparent md:border-0 md:hover:text-blue-700 md:p-0 dark:text-white md:dark:hover:text-blue-500 dark:hover:bg-gray-700 dark:hover:text-white md:dark:hover:bg-transparent";
  };

  const tabList = tabs.map((tab, index) => (
    <li
      key={index}
      className={tabStyle(index)}
      onClick={() => handleClick(index)}
    >
      {tab.name}
    </li>
  ));

  return (
    <>
      <nav className="max-w-screen-xl flex flex-wrap items-center justify-between mx-auto p-4">
        <Link href="/" className="flex items-center">
          <Img src={agroluxLogo} className="h-16 w-16 mr-4" alt="Agrolux" />
          <span className="self-center text-4xl font-semibold whitespace-nowrap dark:text-white">
            Agrolux
          </span>
        </Link>
        <div className="hidden w-full md:block md:w-auto">
          <ul className="font-medium text-xl flex flex-col p-4 md:p-0 mt-4 md:flex-row md:space-x-8 md:mt-0">
            {tabList}
          </ul>
        </div>
      </nav>
    </>
  );
}
