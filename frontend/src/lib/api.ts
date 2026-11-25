export type Input = { nitrogen:number; phosphorus:number; potassium:number; ph:number; temperature_c:number; humidity_pct:number; rainfall_mm:number; soil_type?:string; location?:string; growing_season?:string };
export type CropResult = { crop:string; score:number; matched_parameters:number; total_parameters:number; evidence:{parameter:string;label:string;value:number;observed_min:number;observed_max:number;match:boolean;status:'low'|'ok'|'high';ideal_min:number;ideal_max:number}[]; provenance:string; record_count:number; status:string };
const base = (import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? '/api' : 'http://localhost:8000/api')).replace(/\/+$/, '');
export async function recommend(input:Input):Promise<{recommendation_id:number;results:CropResult[];method:string;interpretation:string;assumptions:string[];unavailable_information:string[];dataset_provenance:string}> {
 const response = await fetch(`${base}/recommendations`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(input)});
 if (!response.ok) { const payload = await response.json().catch(()=>({})); throw new Error(payload.detail ? JSON.stringify(payload.detail) : `Request failed (${response.status})`); }
 return response.json();
}
export async function health():Promise<{status:string;database:string}> { const r=await fetch(`${base}/health`); if(!r.ok) throw new Error('API unavailable'); return r.json(); }
