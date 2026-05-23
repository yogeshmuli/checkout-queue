import { Navigate, Route, Routes } from 'react-router-dom';

import { CreateToken } from './pages/CreateToken.jsx';
import { InvalidToken } from './pages/InvalidToken.jsx';
import { StoreZoneSelect } from './pages/StoreZoneSelect.jsx';
import { TokenLookup } from './pages/TokenLookup.jsx';
import { TokenStatus } from './pages/TokenStatus.jsx';

export function TrialCustomerApp() {
  return (
    <Routes>
      <Route path="/" element={<StoreZoneSelect />} />
      <Route path="/create" element={<CreateToken />} />
      <Route path="/status" element={<TokenLookup />} />
      <Route path="/status/lookup" element={<TokenLookup />} />
      <Route path="/status/:tokenId" element={<TokenStatus />} />
      <Route path="/invalid-token" element={<InvalidToken />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
