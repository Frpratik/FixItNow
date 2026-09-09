const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export function createMechanicSocket(mechanicId, onMessage, onOpen, onClose) {
  const token = localStorage.getItem('fixitnow_access_token');
  if (!token) return null;

  const url = `${WS_BASE_URL}/ws/mechanic/${mechanicId}?token=${encodeURIComponent(token)}`;
  const socket = new WebSocket(url);

  socket.onopen = () => {
    console.log(`[Mechanic WS] Connected: ${mechanicId}`);
    if (onOpen) onOpen();
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (onMessage) onMessage(data);
    } catch (e) {
      console.error('[Mechanic WS] Parse error:', e);
    }
  };

  socket.onerror = (error) => {
    console.warn('[Mechanic WS] Error:', error);
  };

  socket.onclose = () => {
    console.log('[Mechanic WS] Disconnected');
    if (onClose) onClose();
  };

  return socket;
}

export function createCustomerBookingSocket(bookingId, onMessage, onOpen, onClose) {
  const token = localStorage.getItem('fixitnow_access_token');
  if (!token) return null;

  const url = `${WS_BASE_URL}/ws/customer/${bookingId}?token=${encodeURIComponent(token)}`;
  const socket = new WebSocket(url);

  socket.onopen = () => {
    console.log(`[Customer WS] Connected for booking: ${bookingId}`);
    if (onOpen) onOpen();
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (onMessage) onMessage(data);
    } catch (e) {
      console.error('[Customer WS] Parse error:', e);
    }
  };

  socket.onerror = (error) => {
    console.warn('[Customer WS] Error:', error);
  };

  socket.onclose = () => {
    console.log('[Customer WS] Disconnected');
    if (onClose) onClose();
  };

  return socket;
}
