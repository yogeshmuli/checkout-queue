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
        className={`fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 ${modalOpen ? "" : "pointer-events-none opacity-0"}`}
      >
        <div className="bg-white rounded-lg p-6 w-full max-w-xl mx-4 flex flex-col items-end">
            {/* close Icon button */}
            <button
              className="ml-auto text-gray-500 hover:text-gray-700 focus:outline-none"
              onClick={closeModal}
            >
              <span className="sr-only">Close</span>
              &times;
            </button>
          <DemoTools />
        
        </div>
      </div>
      <div className="fixed bottom-4 right-4">
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
