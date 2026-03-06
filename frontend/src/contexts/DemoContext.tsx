/* eslint-disable react-refresh/only-export-components -- context files export both Provider and hook by convention */
import React, { createContext, useContext } from 'react';

interface DemoContextType {
  isDemoMode: boolean;
}

const DemoContext = createContext<DemoContextType>({ isDemoMode: false });

export const useDemoMode = () => useContext(DemoContext);

export const DemoProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <DemoContext.Provider value={{ isDemoMode: true }}>
    {children}
  </DemoContext.Provider>
);
