# 🚀 PHASE 3.5.4 EXECUTION PLAN

## 🎯 Objective
End-to-end testing of WebSocket integration with complete validation of real-time ETo calculation functionality.

**Status**: 🔄 **IN PROGRESS**

---

## 📊 Test Scenarios Overview

### Scenario 1: Happy Path ✅
- **Focus**: Valid coordinates, successful calculation
- **Duration**: 5-10 minutes per run
- **Success Rate Target**: 100%

### Scenario 2: Error Handling ⚠️
- **Focus**: Invalid inputs, error messages
- **Duration**: 2-3 minutes
- **Success Rate Target**: 100% (proper error display)

### Scenario 3: Network Issues 🌐
- **Focus**: Connection loss, reconnection
- **Duration**: 3-5 minutes
- **Success Rate Target**: 100% (graceful recovery)

### Scenario 4: Data Integrity ✔️
- **Focus**: Result accuracy, data completeness
- **Duration**: 5-10 minutes
- **Success Rate Target**: 100% (data matches expected)

### Scenario 5: UI Response 🎨
- **Focus**: Button states, modal behavior, language switching
- **Duration**: 3-5 minutes
- **Success Rate Target**: 100% (responsive UI)

### Scenario 6: Cleanup 🧹
- **Focus**: WebSocket disconnect, memory cleanup
- **Duration**: 2-3 minutes
- **Success Rate Target**: 100% (no memory leaks)

---

## ⏱️ Estimated Timeline

| Scenario | Duration | Notes |
|----------|----------|-------|
| Setup | 5 min | Start services |
| Scenario 1 | 10 min | Full calculation |
| Scenario 2 | 3 min | Error tests |
| Scenario 3 | 5 min | Network tests |
| Scenario 4 | 10 min | Data verification |
| Scenario 5 | 5 min | UI responsiveness |
| Scenario 6 | 3 min | Cleanup verification |
| **Total** | **~45 min** | All scenarios |

---

## 🛠️ Prerequisites

### 1. Services Running
```bash
# Terminal 1: Backend
cd backend
python -m uvicorn backend.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
python -m gunicorn -w 4 -b 127.0.0.1:8050 "app:server"

# Terminal 3: Celery
cd backend
celery -A backend.core.celery_config worker -l info

# Terminal 4: Redis
redis-cli
```

### 2. Verify All Services
```bash
# Backend
curl -s http://localhost:8000/docs > /dev/null && echo "✅ Backend OK" || echo "❌ Backend DOWN"

# Frontend
curl -s http://localhost:8050/ > /dev/null && echo "✅ Frontend OK" || echo "❌ Frontend DOWN"

# Redis
redis-cli ping && echo "✅ Redis OK" || echo "❌ Redis DOWN"
```

### 3. Browser Setup
- Modern browser (Chrome, Firefox, Edge)
- Developer Tools open (F12)
- Network tab visible
- Console tab monitored

---

## 📝 Test Execution Checklist

### Pre-Test
- [ ] All services running
- [ ] Browser at http://localhost:8050/
- [ ] Developer console open
- [ ] Network tab monitoring enabled
- [ ] Test notes ready

### During Tests
- [ ] Note any errors or warnings
- [ ] Take screenshots of anomalies
- [ ] Monitor network traffic
- [ ] Check WebSocket connection
- [ ] Verify progress updates

### Post-Test
- [ ] Document results
- [ ] Identify failures
- [ ] Create bug reports if needed
- [ ] Check cleanup (close modals, disconnect)

---

## 🔍 Detailed Test Procedures

### SCENARIO 1: Happy Path - Valid Coordinates

**Objective**: Complete calculation with real-time progress

**Test Steps**:

1. **Open Application**
   ```
   URL: http://localhost:8050/eto
   Expected: ETo calculator page loads
   ```

2. **Select Location on Map**
   ```
   Action: Click on São Paulo area (~-23.55, -46.63)
   Expected: 
   - Marker appears on map
   - "Click Info" shows coordinates
   - Location is valid (green border)
   ```

3. **Start Calculation**
   ```
   Action: Click "Calculate ETo Today" button
   Expected:
   - Button becomes disabled
   - Modal opens immediately
   - Title: "Cálculo de ETo - Hoje (Em Tempo Real)"
   ```

4. **Monitor Real-time Progress**
   ```
   Expected (every 2 seconds):
   - Progress updates in ProgressCard
   - Status messages change:
     * PROCESSING → "Baixando dados..."
     * Percentages increase: 25%, 50%, 75%, 100%
   - No lag or freezing
   - No console errors
   ```

5. **Wait for Completion**
   ```
   Duration: 5-10 minutes depending on data
   Expected:
   - Status changes to SUCCESS (green)
   - Progress reaches 100%
   - Results table appears
   - Shows columns: Date, ETo, Quality, Source
   ```

6. **Verify Results**
   ```
   Check:
   - Results not empty
   - ETo values are positive
   - Dates match requested period
   - All rows have data
   ```

7. **Close Modal**
   ```
   Action: Click [Fechar] button
   Expected:
   - Modal closes cleanly
   - WebSocket disconnects
   - Map returns to normal state
   - Button re-enables
   ```

**Success Criteria** ✅:
- Modal opens immediately (< 100ms)
- Progress updates every 2 seconds
- No console errors
- Results displayed correctly
- WebSocket disconnects cleanly
- Button re-enables after calculation

**Failure Scenarios**:
- ❌ Modal doesn't open → Check WebSocket connection
- ❌ No progress updates → Check network tab
- ❌ Results not showing → Check browser console
- ❌ Calculation times out → Check backend/Celery

---

### SCENARIO 2: Error Handling - Invalid Inputs

**Objective**: Verify proper error messages and recovery

**Test Steps**:

1. **No Location Selected**
   ```
   Action: Click "Calculate ETo Today" without selecting location
   Expected:
   - Error message appears
   - Modal NOT opened
   - Proper validation message shown
   ```

2. **Invalid Coordinates**
   ```
   Action: Select location outside valid area (high mountains, ocean)
   Expected:
   - Error message: "Invalid coordinates"
   - Cannot proceed to calculation
   ```

3. **No Data Available**
   ```
   Action: Select location with no climate data
   Expected:
   - Modal opens, shows LOADING
   - After timeout: ERROR status (red)
   - Error message: "No data available..."
   - User can close modal and retry
   ```

4. **Network Error**
   ```
   Action: Turn off WiFi/Network during calculation
   Expected:
   - After timeout: ERROR status (red)
   - Error message displayed
   - Option to retry
   ```

**Success Criteria** ✅:
- All error messages clear and helpful
- No unexpected errors in console
- User can recover from errors
- Application remains stable

---

### SCENARIO 3: Network Issues - Connection Loss

**Objective**: Verify graceful handling of network problems

**Test Steps**:

1. **Disconnect WebSocket**
   ```
   Browser DevTools → Network tab
   Action: Block WebSocket connection
   Expected:
   - Modal shows loading
   - After 30s: Error displayed
   - Offers to close or retry
   ```

2. **Reconnect WebSocket**
   ```
   Action: Re-enable network
   Expected:
   - Manual retry button works
   - Reconnection successful
   - Calculation resumes (or restarts)
   ```

3. **Connection Timeout**
   ```
   Action: Intentionally delay response
   Expected:
   - Timeout handling after 30s
   - Proper error message
   - Graceful degradation
   ```

**Success Criteria** ✅:
- Connection loss handled gracefully
- No permanent errors
- Reconnection works
- User informed of issues

---

### SCENARIO 4: Data Integrity - Results Verification

**Objective**: Verify calculation results are accurate

**Test Steps**:

1. **Run Calculation**
   ```
   Location: São Paulo (-23.55, -46.63)
   Date: Today
   ```

2. **Verify Results Structure**
   ```
   Expected columns:
   - Date (YYYY-MM-DD format)
   - ETo (numeric, mm/day)
   - Quality (HIGH/MEDIUM/LOW)
   - Source (data_source name)
   ```

3. **Check Data Consistency**
   ```
   Verify:
   - All rows have complete data
   - No empty cells
   - ETo values reasonable (0.1 to 15 mm/day)
   - Dates sequential
   - No duplicates
   ```

4. **Compare with Expected**
   ```
   If possible:
   - Compare ETo values with known data
   - Verify weather inputs reasonable
   - Check data sources
   ```

**Success Criteria** ✅:
- All data present
- Values within expected range
- No obvious errors
- Data consistent across runs

---

### SCENARIO 5: UI Response - Button States & Language

**Objective**: Verify UI responsiveness and language switching

**Test Steps**:

1. **Button States During Calculation**
   ```
   Initial: Button enabled, shows "Calculate ETo Today"
   During: Button disabled, shows loading state
   After: Button enabled again, ready for next calculation
   ```

2. **Modal Behavior**
   ```
   Check:
   - Smooth opening animation
   - Responsive to window resize
   - Close button always visible
   - Progress bar smooth animation
   ```

3. **Language Switching**
   ```
   Action: Switch language to English (navbar dropdown)
   Expected:
   - UI text updates immediately
   - No page reload
   - Language persists (localStorage)
   - Works during calculation
   ```

4. **Responsive Design**
   ```
   Test different screen sizes:
   - Desktop (1920x1080)
   - Tablet (768x1024)
   - Mobile (375x667)
   
   Expected: All properly positioned
   ```

**Success Criteria** ✅:
- Button states change correctly
- Modal animations smooth
- Language switching works
- UI responsive on all sizes

---

### SCENARIO 6: Cleanup & Performance

**Objective**: Verify proper resource cleanup

**Test Steps**:

1. **Memory Monitoring**
   ```
   Browser DevTools → Memory tab
   Before: Note current memory usage
   After calculation: Note memory usage
   Expected: No significant memory increase
   ```

2. **WebSocket Cleanup**
   ```
   Browser DevTools → Network tab
   Action: Close modal
   Expected:
   - WebSocket connection closes (status 1000)
   - No lingering connections
   - Clean disconnect
   ```

3. **Multiple Calculations**
   ```
   Action: Run 3 calculations in sequence
   Expected:
   - Each calculation succeeds
   - No memory buildup
   - Performance consistent
   - No connection accumulation
   ```

4. **Long-running Calculation**
   ```
   Action: Leave calculation running for full duration
   Expected:
   - No timeouts
   - Memory stable
   - CPU usage reasonable
   - Completes successfully
   ```

**Success Criteria** ✅:
- WebSocket disconnects properly
- No memory leaks
- Multiple calculations work
- Performance consistent

---

## 📋 Result Documentation Template

### Test Run: [Date/Time]

```
SCENARIO 1: Happy Path
Status: ✅ PASS / ⚠️ FAIL
Issues: None / [List issues]
Notes: [Any observations]

SCENARIO 2: Error Handling
Status: ✅ PASS / ⚠️ FAIL
Issues: None / [List issues]
Notes: [Any observations]

SCENARIO 3: Network Issues
Status: ✅ PASS / ⚠️ FAIL
Issues: None / [List issues]
Notes: [Any observations]

SCENARIO 4: Data Integrity
Status: ✅ PASS / ⚠️ FAIL
Issues: None / [List issues]
Notes: [Any observations]

SCENARIO 5: UI Response
Status: ✅ PASS / ⚠️ FAIL
Issues: None / [List issues]
Notes: [Any observations]

SCENARIO 6: Cleanup
Status: ✅ PASS / ⚠️ FAIL
Issues: None / [List issues]
Notes: [Any observations]

OVERALL: ✅ ALL PASS / ⚠️ SOME ISSUES
```

---

## 🔧 Troubleshooting Guide

### Problem: WebSocket Not Connecting
```
Check:
1. Backend running? (curl http://localhost:8000/docs)
2. Frontend running? (curl http://localhost:8050/)
3. Firewall blocking WebSocket? (Check Network tab)
4. Correct WebSocket URL? (Should be ws://localhost:8000/ws/[task_id])

Solution: Restart all services
```

### Problem: Slow/No Progress Updates
```
Check:
1. Backend Celery worker running? (Should see "Worker ready" message)
2. Redis running? (redis-cli ping should return PONG)
3. Network latency? (Check Network tab in DevTools)

Solution: Restart Celery and Redis
```

### Problem: Results Not Displaying
```
Check:
1. Console errors? (F12 → Console tab)
2. Results data returned? (Check Network tab → WebSocket messages)
3. Data formatting correct? (Check JSON structure)

Solution: Check backend logs for calculation errors
```

### Problem: High Memory Usage
```
Check:
1. Previous WebSocket connections closed? (Network tab)
2. DOM elements cleaned up? (DevTools Elements tab)
3. Event listeners removed? (Memory tab snapshot)

Solution: Close all modals, restart browser if needed
```

---

## ✅ Phase Completion Criteria

**PHASE 3.5.4 is COMPLETE when**:
- ✅ All 6 scenarios pass
- ✅ No critical errors
- ✅ WebSocket performs reliably
- ✅ UI responsive and stable
- ✅ Results accurate
- ✅ Cleanup proper
- ✅ Documentation updated

---

## 📚 Related Documentation

- `PHASE_3_5_3_5_CLEANUP_TRANSLATION_COMPLETE.md` - Previous cleanup phase
- `PHASE_3_5_3_WEBSOCKET_INTEGRATION.md` - WebSocket architecture
- `PHASE_3_5_3_ARCHITECTURE.md` - System design

---

**Status**: 🔄 **IN PROGRESS**

**Next**: Execute test scenarios and document results

*For detailed test procedures, see individual scenario sections above.*
