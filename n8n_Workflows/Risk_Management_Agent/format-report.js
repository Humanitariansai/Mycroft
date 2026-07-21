// Extracted body of the n8n "Format Report" Code node so it can be unit-tested
// outside of n8n. Keep the two functions below byte-identical to the jsCode in
// Json_code -> "Format Report". In n8n the node ends with:
//   return formatReport($input.item.json, $('Prepare for LLM').item.json);
// Here we export the functions instead.

function scoreToRating(riskScore) {
  const score = Number(riskScore);
  if (score >= 100) return 'D';
  if (score >= 85) return 'CC';
  if (score >= 70) return 'CCC';
  if (score >= 55) return 'B';
  if (score >= 40) return 'BB';
  if (score >= 30) return 'BBB';
  if (score >= 20) return 'A';
  if (score >= 10) return 'AA';
  return 'AAA';
}

function formatReport(llmInput, prepareNodeJson) {
  const llmResponse = llmInput?.choices?.[0]?.message?.content || 'Analysis pending';

  if (!prepareNodeJson || !prepareNodeJson.original_data) {
    throw new Error('Cannot find original risk data from previous nodes');
  }

  const originalData = prepareNodeJson.original_data;

  let alertLevel = 'INFO';
  if (originalData.risk.risk_score >= 70) {
    alertLevel = 'CRITICAL';
  } else if (originalData.risk.risk_score >= 40) {
    alertLevel = 'WARNING';
  } else if (originalData.risk.risk_score >= 20) {
    alertLevel = 'MONITOR';
  }

  const timestamp = new Date().toISOString();
  const riskFactorsText = originalData.risk.risk_factors.join(', ') || 'None';

  return {
    timestamp: timestamp,
    ticker: originalData.ticker,
    risk_score: originalData.risk.risk_score,
    alert_level: alertLevel,
    current_price: originalData.metrics.current_price,
    position_value: originalData.metrics.position_value,
    unrealized_pl: originalData.performance.unrealized_pl,
    risk_factors: riskFactorsText,
    action: originalData.recommendation.action,
    urgency: originalData.recommendation.urgency,
    position_percent: originalData.metrics.position_percent,
    stop_loss_price: originalData.risk.stop_loss_price,
    volatility: originalData.performance.volatility,
    ai_analysis: llmResponse,
    camelCaseReport: {
      timestamp: timestamp,
      ticker: originalData.ticker,
      riskScore: originalData.risk.risk_score,
      alertLevel: alertLevel,
      currentPrice: originalData.metrics.current_price,
      positionValue: originalData.metrics.position_value,
      unrealizedPl: originalData.performance.unrealized_pl,
      riskFactors: riskFactorsText,
      action: originalData.recommendation.action,
      urgency: originalData.recommendation.urgency,
      positionPercent: originalData.metrics.position_percent,
      stopLossPrice: originalData.risk.stop_loss_price,
      volatility: originalData.performance.volatility,
      aiAnalysis: llmResponse,
      creditRating: scoreToRating(originalData.risk.risk_score)
    }
  };
}

module.exports = { formatReport, scoreToRating };
