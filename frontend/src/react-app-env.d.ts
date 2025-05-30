/// <reference types="react" />
/// <reference types="react-dom" />

declare namespace React {
  interface ReactNode {
    children?: ReactNode;
  }
}

declare module 'react/jsx-runtime';
