# 🧪 PHASE 3.5.4: WebSocket E2E Testing Guide

## ✅ Ready to Test

All WebSocket integration components are complete and ready for end-to-end testing.

---

## 📋 Test Environment Setup

### Prerequisites

```bash
# 1. Backend running
cd backend
python -m uvicorn backend.main:app --reload --port 8000

# 2. Frontend running
cd frontend
python -m gunicorn -w 4 -b 127.0.0.1:8050 "app:server"

# 3. Celery worker running (for async tasks)
cd backend
celery -A backend.core.celery_config worker -l info

# 4. Redis running (for message pub/sub)
redis-cli  # or redis-server on another terminal

# 5. Browser: http://localhost:8050/
```

### Verify Components

```bash
# Check backend is serving
curl http://localhost:8000/docs

# Check frontend is up
curl http://localhost:8050/

# Check WebSocket endpoint
websocat ws://localhost:8000/ws/test-connection
# Should echo back or timeout (expected)
```

---

## 🎯 Test Scenarios

### SCENARIO 1: Happy Path - Valid Coordinates ✅

**Objective**: Complete calculation with real-time progress

**Steps**:
1. Open http://localhost:8050/
2. Click on world map to select a location
   - Try: São Paulo, Brazil (-23.55, -46.63)
   - Or any valid coordinate within bounds
3. Verify coordinates appear in "Click Info"
4. Click "Calculate ETo Today" button

**Expected Behavior**:
```
✓ Modal opens with title "Cálculo de ETo - Hoje (Em Tempo Real)"
✓ ProgressCard shows PROCESSING status
✓ Location coordinates displayed
✓ Progress bar appears (should be at ~5%)

Wait 2-3 seconds:
✓ Step updates: "Baixando dados..." → shows progress (25%, 50%, 75%, etc)
✓ Progress bar animates smoothly
✓ Every 2 seconds: new message received

Wait for completion (5-10 minutes):
✓ Status changes to SUCCESS (green)
✓ Progress reaches 100%
✓ Results table appears with data:
  - Column 1: Date
  - Column 2: ETo value (mm)
  - Column 3: Quality (HIGH/MEDIUM/LOW)
  - Column 4: Data source (open_meteo/nasa_power/etc)

✓ [Exportar Resultados] button appears
✓ [Fechar] button closes modal
```

**Success Criteria** ✅:
- Modal opened immediately
- Real-time progress updates every 2 seconds
- Final results displayed
- No console errors
- WebSocket disconnected cleanly

**Browser Console Check**:
```javascript
// Should see logs like:
// 🟢 Iniciando cálculo ETo hoje
// 📡 POST /internal/eto/eto_calculate
// ✅ Task criada: task_id=abc-123
// 🔗 WebSocket conectado: abc-123
// 📊 Modal aberto com ProgressCard
// 🔄 Verificando WebSocket task_id: status=connected
// 📨 WebSocket PROGRESS: step=Baixando dados, progress=25
// 📊 Atualizado: status=PROCESSING, progress=25%
// ... (repeat every 2 seconds)
// ✅ Tarefa finalizada: task_id=abc-123 (SUCCESS)
```

---

### SCENARIO 2: Invalid Coordinates ❌

**Objective**: Verify error handling for invalid input

**Steps**:
1. Open Browser DevTools (F12 → Console)
2. Manually inject invalid location data:
   ```javascript
   // In browser console:
   dash.Store.setData('selected-location', {
     lat: 150,  // Invalid: > 90
     lng: -46.63,
     elevation: 700
   });
   ```
3. Click "Calculate ETo Today" button

**Expected Behavior**:
```
✓ Modal opens
✓ ProgressCard shows PROCESSING
✓ Status immediately changes to ERROR (red)
✓ Error message displayed:
  "A latitude deve estar entre -90 e 90 graus."

✓ No results table (error state)
✓ [Fechar] button closes modal
```

**Success Criteria** ✅:
- Error caught at API level
- Modal shows ERROR status with message
- No WebSocket connection (error before task creation)
- User can close modal
- No unhandled exceptions

**Browser Console Check**:
```javascript
// Should see:
// ❌ Erro na requisição: 422 Unprocessable Entity
// Title: "Erro no Cálculo"
// Body: "Erro ao conectar com o servidor: ..."
```

---

### SCENARIO 3: Network Timeout 🔌

**Objective**: Test timeout handling and recovery

**Steps**:
1. Open http://localhost:8050/
2. Stop the backend server:
   ```bash
   # Ctrl+C in backend terminal
   ```
3. Select location and click "Calculate ETo Today"

**Expected Behavior**:
```
✓ Modal opens
✓ Attempt to POST to API fails after 10 seconds (timeout)
✓ ProgressCard shows ERROR status
✓ Error message:
  "Erro ao conectar com o servidor: Connection refused"

✓ User can close modal and retry
```

**Success Criteria** ✅:
- Request times out gracefully
- Error message is informative
- No hanging/freezing UI
- Modal can be closed
- User can retry after restarting backend

**Restart Backend**:
```bash
# Restart backend
python -m uvicorn backend.main:app --reload --port 8000

# Try again - should work now
```

---

### SCENARIO 4: Close Modal During Calculation 🔴

**Objective**: Verify WebSocket cleanup when user cancels

**Steps**:
1. Select location
2. Click "Calculate ETo Today"
3. Wait for modal to show PROCESSING status
4. Wait 5-10 seconds
5. Click "Fechar" button to close modal

**Expected Behavior**:
```
✓ Modal closes immediately
✓ WebSocket disconnection message in console:
  "🔌 Desconectado task_id: status=connected, mensagens=2"

✓ No further updates after modal closes
✓ Backend Celery task continues (in background)
✓ No memory leaks (connection cleaned up)

Check in 1 minute:
✓ Backend task still running in background (normal)
✓ No orphaned WebSocket connections
✓ No error messages
```

**Success Criteria** ✅:
- Modal closes cleanly
- WebSocket disconnected
- No UI freeze
- Task continues (expected behavior)
- Cleanup is immediate

**Check Active Connections**:
```python
# In Python terminal:
from frontend.utils.websocket_handler import WebSocketConnectionManager
manager = WebSocketConnectionManager()
print(manager.get_connection_stats())
# Should show: {"active_connections": 0, ...}
```

---

### SCENARIO 5: Multiple Parallel Calculations 🔀

**Objective**: Verify system handles multiple simultaneous tasks

**Steps**:
1. Select location 1 (e.g., São Paulo, -23.55, -46.63)
2. Click "Calculate ETo Today"
3. Wait for modal to show PROCESSING
4. Open a NEW browser tab
5. In new tab: http://localhost:8050/
6. Select location 2 (e.g., Rio de Janeiro, -22.91, -43.17)
7. Click "Calculate ETo Today"
8. In new tab: modal should open with PROCESSING

**Expected Behavior**:
```
Tab 1:
✓ Modal 1 shows PROCESSING
✓ Real-time updates from task 1
✓ Message: "Task criada: task_id=abc-123"

Tab 2:
✓ Modal 2 shows PROCESSING (different from Modal 1)
✓ Real-time updates from task 2
✓ Message: "Task criada: task_id=xyz-789"

✓ Both tasks progress independently
✓ No cross-talk between tasks
✓ Each has separate WebSocket connection

Wait for completion:
✓ Tab 1: Results appear first or second (depending on speed)
✓ Tab 2: Results appear
✓ No data mixing between results
```

**Success Criteria** ✅:
- Multiple WebSocket connections simultaneous
- Each has separate task_id
- No data corruption
- Both calculate independently
- Results are correct for each location

**Terminal Check**:
```bash
# In backend terminal, should see:
# 🔗 Thread de conexão WebSocket iniciada: abc-123
# ✅ WebSocket conectado: abc-123
# 🔗 Thread de conexão WebSocket iniciada: xyz-789
# ✅ WebSocket conectado: xyz-789
# ... (separate progress for each)
```

---

### SCENARIO 6: Browser Console - No Errors 🚫

**Objective**: Verify no JavaScript errors during operation

**Steps**:
1. Open browser DevTools (F12 → Console)
2. Run any of the above scenarios (preferably Scenario 1)
3. Observe console throughout entire process

**Expected Behavior**:
```
Console should show:
✓ Informational messages (prefixed with 📡, 🟢, ✅, 🔄)
✓ NO red errors (❌)
✓ NO yellow warnings (⚠️)
✓ NO JavaScript exceptions

Filter by: Console level
✓ Errors: 0
✓ Warnings: 0
```

**Common Issues** (If Seen):
```javascript
// ❌ ERROR: "Uncaught TypeError: Cannot read property 'task_id' of null"
//    → Check if calculation-state is initialized in app.py

// ❌ ERROR: "WebSocket connection failed"
//    → Check if WebSocket service is running (port 8000)

// ⚠️ WARNING: "Deprecation: setInterval..."
//    → Normal, from dcc.Interval component

// ⚠️ WARNING: "React doesn't recognize the X prop"
//    → Normal, from Bootstrap component
```

---

## 📊 Test Matrix

| Scenario | Input | Expected | Status | Notes |
|----------|-------|----------|--------|-------|
| 1. Happy Path | Valid coords | SUCCESS + results | ✅ TO TEST | Main flow |
| 2. Invalid Coords | lat > 90 | ERROR message | ✅ TO TEST | Validation |
| 3. Network Error | Backend down | Timeout + Error | ✅ TO TEST | Recovery |
| 4. Close Mid-Calc | Click Close | WebSocket cleanup | ✅ TO TEST | Cleanup |
| 5. Parallel Tasks | 2 tabs × 2 locs | Independent progress | ✅ TO TEST | Threading |
| 6. No Errors | Any scenario | Console clear | ✅ TO TEST | Quality |

---

## 🔍 Debugging Tools

### 1. Browser DevTools

**Network Tab**:
```
Filter: ws
- Shows WebSocket connections
- ws://localhost:8000/ws/task_status/{task_id}
- Messages tab shows real-time data
```

**Console Tab**:
```
- Shows all logger output
- Error tracking
- Manual testing
```

### 2. Backend Logs

```bash
# Watch backend logs
tail -f backend/logs/api.log

# Look for patterns:
# ✅ Task criada: task_id=...
# 📨 ETo calculation task initiated
# 🔗 WebSocket conectado
```

### 3. Celery Monitoring

```bash
# In separate terminal:
celery -A backend.core.celery_config events

# Shows:
# - Task state changes
# - Progress updates
# - Task completion
```

### 4. Redis Monitoring

```bash
# In Redis CLI:
redis-cli
SUBSCRIBE task_*

# Shows messages published by Celery tasks
```

### 5. Python Interactive Testing

```python
# In Python terminal:
from frontend.utils.websocket_handler import WebSocketConnectionManager

manager = WebSocketConnectionManager()

# Simulate WebSocket connection
async def test():
    await manager._receive_messages("test-task", callback=print)

# Check stats
manager.get_connection_stats()
# Output: {"active_connections": 1, ...}
```

---

## 🎬 Test Execution Plan

### Quick Test (15 minutes)
```bash
# 1. All prerequisites running
# 2. Run Scenario 1 (Happy Path)
# 3. Verify results appear
# 4. Check console for no errors
# Done! ✅
```

### Standard Test (45 minutes)
```bash
# 1. Scenario 1: Happy Path
# 2. Scenario 2: Invalid Coords
# 3. Scenario 3: Network Timeout (optional)
# 4. Scenario 4: Close Modal
# 5. All console checks passed
# Done! ✅
```

### Comprehensive Test (2 hours)
```bash
# 1. All Quick Test scenarios
# 2. Scenario 3: Network Timeout
# 3. Scenario 5: Parallel Calculations
# 4. Scenario 6: Console validation
# 5. Check logs and Redis
# 6. Verify performance stats
# Done! ✅✅✅
```

---

## 📋 Test Checklist

### Phase 3.5.4 - WebSocket E2E Testing

- [ ] **Prerequisites**
  - [ ] Backend running (port 8000)
  - [ ] Frontend running (port 8050)
  - [ ] Celery worker active
  - [ ] Redis active
  - [ ] Browser at http://localhost:8050/

- [ ] **Scenario 1: Happy Path**
  - [ ] Modal opens immediately
  - [ ] PROCESSING status shown
  - [ ] Real-time updates (every 2s)
  - [ ] Results appear on SUCCESS
  - [ ] No console errors

- [ ] **Scenario 2: Invalid Coordinates**
  - [ ] Error caught before WebSocket
  - [ ] Error message displayed
  - [ ] Modal can close
  - [ ] No unhandled exceptions

- [ ] **Scenario 3: Network Timeout**
  - [ ] Backend stopped
  - [ ] Request times out (10s)
  - [ ] Error shown to user
  - [ ] Can retry after backend restart

- [ ] **Scenario 4: Close During Calc**
  - [ ] Modal closes immediately
  - [ ] WebSocket disconnects
  - [ ] No memory leak
  - [ ] Backend task continues

- [ ] **Scenario 5: Parallel Tasks**
  - [ ] Multiple tabs open
  - [ ] Each has separate task_id
  - [ ] Independent progress
  - [ ] No data mixing

- [ ] **Scenario 6: Console Validation**
  - [ ] No JavaScript errors
  - [ ] No warnings
  - [ ] Informational messages only
  - [ ] Clean shutdown

### Test Results

| Scenario | Result | Notes |
|----------|--------|-------|
| 1. Happy Path | ✅ / ❌ | |
| 2. Invalid Coords | ✅ / ❌ | |
| 3. Network Error | ✅ / ❌ | |
| 4. Close Modal | ✅ / ❌ | |
| 5. Parallel Tasks | ✅ / ❌ | |
| 6. Console Clear | ✅ / ❌ | |

---

## 🐛 Known Issues & Workarounds

### Issue: WebSocket Connection Refused

**Symptom**: "ws://localhost:8000/ws/task_status/... failed"

**Cause**: WebSocket service not running

**Fix**:
```bash
# Check backend logs
grep -i websocket backend/logs/api.log

# Restart backend
uvicorn backend.main:app --reload --port 8000
```

### Issue: Modal Doesn't Update

**Symptom**: Progress stuck at 5%, no updates

**Cause**: dcc.Interval not triggering

**Fix**:
```bash
# Check app.py has dcc.Interval
grep -n "websocket-interval" frontend/app.py

# Refresh browser page
# Ctrl+Shift+R (hard refresh)
```

### Issue: Results Show Wrong Data

**Symptom**: Results don't match location selected

**Cause**: task_id mismatch or wrong location stored

**Fix**:
```javascript
// In browser console:
// Clear location store
dash.Store.setData('selected-location', null);
// Try again
```

---

## 📈 Performance Benchmarks

**Expected timings**:
- API response time: < 100ms ✅
- WebSocket connect: < 500ms ✅
- First PROGRESS message: 2-5 seconds ✅
- UI update after message: < 100ms ✅
- Full calculation: 5-10 minutes (depends on data volume)

---

## ✅ Sign-Off

When all tests pass:

```markdown
## ✅ PHASE 3.5.4 COMPLETE

Date: [Today]
Tester: [Your Name]
Status: All scenarios tested ✅

Scenarios Passed:
- [x] Scenario 1: Happy Path
- [x] Scenario 2: Invalid Coords
- [x] Scenario 3: Network Timeout
- [x] Scenario 4: Close Modal
- [x] Scenario 5: Parallel Tasks
- [x] Scenario 6: Console Validation

No blocking issues found.
Ready for PHASE 4: Unit Testing
```

---

**Ready to Test!** 🚀

Start with Scenario 1 for quick validation, then move to comprehensive testing.
