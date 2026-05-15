import { Navigate, Route, Routes } from 'react-router-dom';

import { CreateToken } from './pages/CreateToken.jsx';
import { InvalidToken } from './pages/InvalidToken.jsx';
import { TokenStatus } from './pages/TokenStatus.jsx';

export function CustomerApp() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="create" replace />} />
      <Route path="/create" element={<CreateToken />} />
      <Route path="/status" element={<InvalidToken />} />
      <Route path="/status/:tokenId" element={<TokenStatus />} />
      <Route path="*" element={<Navigate to="create" replace />} />
    </Routes>
  );
}
