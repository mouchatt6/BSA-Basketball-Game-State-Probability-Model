import { createBrowserRouter } from "react-router";
import Dashboard from "./pages/Dashboard";
import PlayerMarketDetail from "./pages/PlayerMarketDetail";
import Portfolio from "./pages/Portfolio";

export const router = createBrowserRouter(
  [
    {
      path: "/",
      element: <Dashboard />,
    },
    {
      path: "/index.html",
      element: <Dashboard />,
    },
    {
      path: "/market/:marketId",
      element: <PlayerMarketDetail />,
    },
    {
      path: "/portfolio",
      element: <Portfolio />,
    },
  ],
  {
    basename: "/win-prob-v2/figma-trading-ui/dist",
  },
);
