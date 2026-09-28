/**
 * "AAAA-MM-DD" do mesmo dia `meses` meses de calendário antes de `fim`, com o dia limitado
 * ao último dia do mês de destino (31/03 − 1 mês = 28/02). Trabalha em data local.
 */
export function inicioHaMeses(fim: Date, meses: number): string {
  const total = fim.getFullYear() * 12 + fim.getMonth() - meses;
  const ano = Math.floor(total / 12);
  const mes = total - ano * 12; // 0–11
  const ultimoDia = new Date(ano, mes + 1, 0).getDate();
  const dia = Math.min(fim.getDate(), ultimoDia);
  return `${ano}-${String(mes + 1).padStart(2, "0")}-${String(dia).padStart(2, "0")}`;
}
