/* Chart-only calculations on the authorized November day-session bars.
 * No trade signals, backtest, broker integration or historical data fetching.
 * Warm-up starts at the first supplied bar; missing warm-up stays null.
 */
'use strict';
function calculateDataset(source) {
  const grouped = {};
  for (const [stamp, o, h, l, c, v] of source.bars) {
    const date = stamp.slice(0,4)+'-'+stamp.slice(4,6)+'-'+stamp.slice(6,8);
    const minute = Number(stamp.slice(8,10))*60+Number(stamp.slice(10,12));
    (grouped[date] ||= []).push([minute,o,h,l,c,v]);
  }
  const dates = Object.keys(grouped).sort();
  const data = {};
  for (const period of [1,3,5,15,30,60,1440]) {
    let flat = [], previousClose = null;
    const days = {};
    for (const date of dates) {
      const result = [], first = grouped[date][0][0];
      let key = null, current = null;
      for (const bar of grouped[date]) {
        const next = period===1440 ? 0 : Math.floor((bar[0]-first)/period);
        if (next!==key) {
          if (current) result.push(current);
          current = bar.slice(); key = next;
        } else {
          current[2]=Math.max(current[2],bar[2]); current[3]=Math.min(current[3],bar[3]);
          current[4]=bar[4]; current[5]+=bar[5];
        }
      }
      if (current) result.push(current);
      for (const row of result) {
        row.length=20;
        for (let i=6;i<20;i++) row[i]=null;
        row[19]=previousClose;
      }
      previousClose = result.at(-1)[4];
      days[date] = result;
      flat.push(...result);
    }
    const closes=[], highs=[], lows=[], volumes=[], rsi5=[];
    let ema12=null, ema26=null, signal=null, k=50, d=50;
    const rsis = {5:{gain:0,loss:0},10:{gain:0,loss:0}};
    const mean=(values,length)=>values.length<length || values.slice(-length).some(v=>!Number.isFinite(v))
      ? null : values.slice(-length).reduce((a,b)=>a+b,0)/length;
    for (let index=0;index<flat.length;index++) {
      const row=flat[index], close=row[4];
      closes.push(close); highs.push(row[2]); lows.push(row[3]); volumes.push(row[5]);
      row[6]=mean(closes,5); row[7]=mean(closes,10); row[8]=mean(closes,20);
      ema12=ema12===null ? close : ema12+(close-ema12)*2/13;
      ema26=ema26===null ? close : ema26+(close-ema26)*2/27;
      const dif=ema12-ema26;
      signal=signal===null ? dif : signal+(dif-signal)*2/10;
      // EMA is seeded with the first supplied close, but not displayed until warm.
      if(index>=33) { row[9]=dif; row[10]=signal; row[11]=dif-signal; }
      if(index>=8) {
        const high=Math.max(...highs.slice(-9)), low=Math.min(...lows.slice(-9));
        const rsv=high===low ? 50 : (close-low)/(high-low)*100;
        k=k*2/3+rsv/3; d=d*2/3+k/3; row[12]=k; row[13]=d;
      }
      for (const length of [5,10]) {
        const state=rsis[length];
        if(index>0) {
          const delta=close-closes[index-1], gain=Math.max(delta,0), loss=Math.max(-delta,0);
          if(index<=length) { state.gain+=gain/length; state.loss+=loss/length; }
          else { state.gain=(state.gain*(length-1)+gain)/length; state.loss=(state.loss*(length-1)+loss)/length; }
        }
        if(index>=length) row[length===5?14:15]=state.gain===0&&state.loss===0 ? 50
          : state.loss===0 ? 100 : 100-100/(1+state.gain/state.loss);
      }
      rsi5.push(row[14]); row[16]=mean(rsi5,14);
      row[17]=mean(volumes,5); row[18]=mean(volumes,10);
    }
    data[period]={days,prior:Array(20).fill(null)};
  }
  return data;
}
if (typeof module!=='undefined') module.exports={calculateDataset};
