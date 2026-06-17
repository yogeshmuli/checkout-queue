import { Navigate, Route, Routes } from 'react-router-dom';

import { CreateToken } from './pages/CreateToken.jsx';
import { InvalidToken } from './pages/InvalidToken.jsx';
import { TokenLookup } from './pages/TokenLookup.jsx';
import { TokenStatus } from './pages/TokenStatus.jsx';
import { StoreSectionSelect } from './pages/StoreSectionSelect.jsx';

export function CustomerApp() {
  debugger
  return (
    <Routes>
      <Route path="/" element={<StoreSectionSelect />} />
      <Route path="/create" element={<CreateToken />} />
      <Route path="/status" element={<TokenLookup />} />
      <Route path="/status/lookup" element={<TokenLookup />} />
      <Route path="/status/:tokenId" element={<TokenStatus />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
