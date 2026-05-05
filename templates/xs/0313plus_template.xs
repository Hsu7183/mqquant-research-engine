// 0313plus simplified XS template
// Rendered by mqquant-research-engine.

Inputs:
    EntryBufferPts({{EntryBufferPts}}),
    DonBufferPts({{DonBufferPts}}),
    ATRStopK({{ATRStopK}}),
    ATRTakeProfitK({{ATRTakeProfitK}}),
    TrailStartPctAnchor({{TrailStartPctAnchor}}),
    TrailGivePctAnchor({{TrailGivePctAnchor}}),
    TimeStopBars({{TimeStopBars}}),
    AnchorBackPct({{AnchorBackPct}});

Variables:
    atrValue(0),
    entryPrice(0),
    stopPrice(0),
    takeProfitPrice(0);

atrValue = Average(TrueRange, 14);
entryPrice = Close + EntryBufferPts + DonBufferPts;
stopPrice = entryPrice - atrValue * ATRStopK;
takeProfitPrice = entryPrice + atrValue * ATRTakeProfitK;

// Strategy body intentionally omitted in template MVP.
