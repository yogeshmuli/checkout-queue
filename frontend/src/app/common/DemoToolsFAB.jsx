import { X } from "lucide-react";
import React from "react";
import DemoTools from "./DemoTools.jsx";

const DemoToolsFAB = () => {
  const [modalOpen, setModalOpen] = React.useState(false);

  function openModal() {
    setModalOpen(true);
  }

  function closeModal() {
    setModalOpen(false);
  }

  return (
    <>
      <div
        className={`fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-0 transition-opacity duration-200 sm:items-center sm:p-4 ${modalOpen ? "" : "pointer-events-none opacity-0"}`}
      >
        <div className="flex max-h-[92vh] w-full flex-col overflow-hidden rounded-t-2xl bg-white shadow-2xl sm:max-w-2xl sm:rounded-2xl">
          <div className="flex shrink-0 items-center justify-between  px-4 py-3">
            <p className="text-sm font-semibold text-charcoal">Demo tools</p>
            <button
              type="button"
              className="rounded-lg p-2 text-gray-500 hover:bg-slate-100 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-soft"
              onClick={closeModal}
              aria-label="Close demo tools"
            >
              <X size={18} />
            </button>
          </div>
          <div className="min-h-0 overflow-y-auto  sm:px-5">
          <DemoTools />
          </div>
        </div>
      </div>
      <div className="fixed bottom-4 right-4 z-40">
        <button
          className="flex items-center gap-2 rounded-full bg-brand-red px-4 py-2 text-white shadow-lg hover:bg-brand-red-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-red"
          onClick={openModal}
        >
          <span>Demo Tools</span>
        </button>
      </div>
    </>
  );
};

export default DemoToolsFAB;
