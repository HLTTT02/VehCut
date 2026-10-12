import { useState } from "react";
import { VehicleAIModulePage, type ModulePage } from "./pages/VehicleAIModulePage";

export default function App() {
  const [page, setPage] = useState<ModulePage>("overview");
  return <VehicleAIModulePage page={page} onNavigate={setPage} />;
}
