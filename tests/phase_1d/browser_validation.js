// Phase 1D Browser Validation Script
// Run this in browser console while dashboard is active
// Validates frontend data consistency with WebSocket messages

console.log('=== Phase 1D: Frontend Data Validation ===\n');

// Test 1: Message Reception
const receivedMessages = [];
let messageCount = 0;
const startTime = Date.now();

// Monitor WebSocket messages
const originalHandler = wsClient.ws.onmessage;
wsClient.ws.onmessage = function(event) {
    const msg = JSON.parse(event.data);
    receivedMessages.push({
        time: Date.now() - startTime,
        type: msg.type,
        tick: msg.tick,
        deltaCount: msg.deltas ? msg.deltas.length : 0
    });
    messageCount++;
    originalHandler.call(this, event);
};

// Wait 10 seconds then analyze
setTimeout(() => {
    console.log(`\n=== Results after 10 seconds ===`);
    console.log(`Total messages: ${messageCount}`);

    const deltas = receivedMessages.filter(m => m.type === 'delta');
    console.log(`Delta messages: ${deltas.length}`);

    // TEST 1: Monotonic tick counter
    let tickErrors = 0;
    for (let i = 1; i < deltas.length; i++) {
        if (deltas[i].tick !== deltas[i-1].tick + 1) {
            console.error(`❌ Tick not monotonic: ${deltas[i-1].tick} → ${deltas[i].tick}`);
            tickErrors++;
        }
    }

    if (tickErrors === 0) {
        console.log('✅ TEST 1 PASS: Tick counter monotonic');
    } else {
        console.error(`❌ TEST 1 FAIL: ${tickErrors} tick errors`);
    }

    // TEST 2: Live cell count consistent
    const liveCellElement = document.getElementById('live-cells');
    const finalLiveCount = parseInt(liveCellElement.textContent);
    console.log(`UI live count: ${finalLiveCount}`);

    // Count actual live cells in DOM
    let domLiveCount = 0;
    const aliveCells = document.querySelectorAll('.cell.alive');
    aliveCells.forEach(cell => { domLiveCount++; });
    console.log(`DOM live count: ${domLiveCount}`);

    if (finalLiveCount === domLiveCount && finalLiveCount === 5) {
        console.log(`✅ TEST 2 PASS: Live cell count correct (${finalLiveCount} == ${domLiveCount} == 5)`);
    } else {
        console.error(`❌ TEST 2 FAIL: Live count mismatch: display=${finalLiveCount}, DOM=${domLiveCount}, expected=5`);
    }

    // TEST 3: Update rate
    const updateRateElement = document.getElementById('update-rate');
    if (updateRateElement) {
        const updateRate = parseFloat(updateRateElement.textContent);
        console.log(`Update rate: ${updateRate} updates/sec`);

        if (1.8 <= updateRate && updateRate <= 2.2) {
            console.log(`✅ TEST 3 PASS: Update rate correct (${updateRate}/sec ≈ 2.0)`);
        } else {
            console.error(`❌ TEST 3 FAIL: Update rate wrong: ${updateRate}/sec (expected ~2.0)`);
        }
    } else {
        console.warn('⚠️  Update rate element not found');
    }

    // TEST 4: Delta sizes reasonable
    if (deltas.length > 0) {
        const avgDeltaSize = deltas.reduce((sum, d) => sum + d.deltaCount, 0) / deltas.length;
        console.log(`Average delta size: ${avgDeltaSize.toFixed(1)} cells/update`);

        if (2 <= avgDeltaSize && avgDeltaSize <= 15) {
            console.log(`✅ TEST 4 PASS: Average delta size reasonable (${avgDeltaSize.toFixed(1)} cells/update)`);
        } else {
            console.warn(`⚠️  TEST 4 WARNING: Average delta size unexpected: ${avgDeltaSize.toFixed(1)}`);
        }
    } else {
        console.warn('⚠️  No delta messages received for TEST 4');
    }

    // TEST 5: Message types expected
    const messageTypes = receivedMessages.map(m => m.type);
    const fullStateCount = messageTypes.filter(t => t === 'full_state').length;
    const deltaCount = messageTypes.filter(t => t === 'delta').length;

    if (fullStateCount >= 1) {
        console.log(`✅ TEST 5 PASS: Full state message sent (received: ${fullStateCount})`);
    } else {
        console.error(`❌ TEST 5 FAIL: No full state message received`);
    }

    console.log(`Message breakdown: ${deltaCount} deltas, ${fullStateCount} full state`);

    console.log('\n=== Frontend Data Validation Complete ===');
    console.log('Copy these results to docs/validation/frontend_data_results.txt');

}, 10000);

console.log('Validation running for 10 seconds...');
console.log('Ensure glider is seeded and running to get accurate results.');
