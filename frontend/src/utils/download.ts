/**
 * 报告下载工具函数
 */

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = sanitizeFilename(filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export function sanitizeFilename(filename: string): string {
  return filename
    .replace(/[\\/:*?"<>|]/g, '_')
    .replace(/\s+/g, ' ')
    .slice(0, 180)
}

export function getFilenameFromDisposition(contentDisposition?: string): string | undefined {
  if (!contentDisposition) return undefined
  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match?.[1]) return decodeURIComponent(utf8Match[1])
  const plainMatch = contentDisposition.match(/filename="?([^";]+)"?/i)
  return plainMatch?.[1]
}

export function buildReportFilename(
  kpi: 'IFIR' | 'RA',
  dimension: 'Model' | 'ODM' | 'Segment',
  entities: string[],
  dateRange: [string, string],
): string {
  const entitiesStr = entities.length <= 3
    ? entities.join('+')
    : `${entities.slice(0, 2).join('+')}等${entities.length}个`
  const range = `${dateRange[0]}至${dateRange[1]}`
  const date = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  return `${kpi}_${dimension}分析报告_${entitiesStr}_${range}_${date}.xlsx`
}

/**
 * 检查返回的 blob 是否为有效的 Excel 文件，否则抛出错误。
 * 后端可能返回 JSON 错误体而非 Excel。
 */
export async function ensureReportBlobOrThrow(blob: Blob) {
  const type = (blob.type || '').toLowerCase()
  const isExcel = type.includes('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
  const isJsonLike = type.includes('json') || type.includes('text/html')

  if (isExcel) return
  if (!isJsonLike && blob.size > 0) return

  const text = await blob.text()
  try {
    const error = JSON.parse(text) as { message?: string; detail?: string }
    throw new Error(error.message || error.detail || text || '报告生成失败')
  } catch {
    const normalized = text.trim()
    if (normalized.startsWith('<')) {
      throw new Error('报告生成失败')
    }
    throw new Error(normalized || '报告生成失败')
  }
}
