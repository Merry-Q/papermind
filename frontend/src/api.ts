export async function api<T>(path:string, options?:RequestInit):Promise<T> {
  const response = await fetch(`/api${path}`, options);
  if (!response.ok) {
    const data = await response.json().catch(()=>({detail:'服务暂时不可用，请稍后重试'}));
    throw new Error(typeof data.detail === 'string' ? data.detail : '请求格式不正确，请检查输入');
  }
  return response.json() as Promise<T>;
}
export const json = (method:string, body:unknown):RequestInit => ({method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
