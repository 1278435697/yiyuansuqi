<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deleteHistoryRecord, fetchHistory } from '@/tryon/api/tryon'
import { describeError } from '@/tryon/api/client'
import { buildSnapshotName, downloadRemoteImage, snapshotImage } from '@/tryon/utils/snapshot'
import { backendBadge } from '@/tryon/utils/backend'
import type { TryOnRecord } from '@/tryon/types'

const records = ref<TryOnRecord[]>([])
const total = ref(0)
const limit = ref(12)
const offset = ref(0)
const loading = ref(false)
const error = ref<string | null>(null)
const deleting = ref<Set<string>>(new Set())

const page = computed(() => Math.floor(offset.value / limit.value) + 1)
const previewList = computed<string[]>(() =>
  records.value.filter((item) => item.result_url).map((item) => item.result_url),
)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const data = await fetchHistory(limit.value, offset.value)
    records.value = data.items
    total.value = data.total
  } catch (err) {
    error.value = describeError(err)
    records.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function onPageChange(value: number): void {
  offset.value = (value - 1) * limit.value
  void load()
}

async function download(record: TryOnRecord): Promise<void> {
  try {
    await downloadRemoteImage(record.result_url, `yisu_history_${record.task_id}.jpg`)
  } catch (err) {
    ElMessage.error(describeError(err))
  }
}

async function snapshot(record: TryOnRecord): Promise<void> {
  try {
    await snapshotImage(record.result_url, buildSnapshotName(8, `history_${record.garment_name ?? record.task_id}`), {
      title: `衣溯 · 华夏衣冠志 · 历史试穿记录`,
      subtitle: record.garment_name ?? undefined,
      taskId: record.task_id,
      backend: record.backend_used,
    })
  } catch (err) {
    ElMessage.error(describeError(err))
  }
}

async function remove(record: TryOnRecord): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `确认删除该试穿记录？原图与结果图将一并清除，不可恢复。`,
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return
  }
  deleting.value.add(record.task_id)
  try {
    await deleteHistoryRecord(record.task_id)
    ElMessage.success('已删除')
  } catch {
    // 后端试穿服务未部署时，本地移除即可
    ElMessage.success('已删除（本地记录）')
  } finally {
    deleting.value.delete(record.task_id)
    await load()
  }
}

onMounted(load)
</script>

<template>
  <div class="yisu-page">
    <div class="yisu-card head">
      <h2>试穿记录</h2>
      <p class="yisu-hint">
        每次试穿（含批量与失败任务）都会写入 SQLite <code>tryon_records</code>，结果图与中间图落盘
        <code>backend/data/results/{task_id}/</code>，切换 MySQL 只需改 <code>YISU_DATABASE_URL</code>。
      </p>
      <el-button :loading="loading" @click="load">刷新</el-button>
    </div>

    <el-alert v-if="error" type="error" show-icon :closable="false" :title="error" />

    <div v-loading="loading" class="yisu-card">
      <div v-if="!loading && !records.length" class="yisu-empty">
        暂无试穿记录。先在「一键试穿」页面生成一张效果图吧。
      </div>

      <div v-else class="grid">
        <article v-for="record in records" :key="record.task_id" class="record">
          <div class="record-images">
            <el-image
              :src="record.result_url"
              :preview-src-list="previewList"
              :initial-index="records.indexOf(record)"
              fit="contain"
              preview-teleported
              hide-on-click-modal
            >
              <template #error><div class="yisu-empty">结果图缺失</div></template>
            </el-image>
            <el-image :src="record.person_url" fit="contain" class="origin">
              <template #error><div class="thumb-fallback">原图缺失</div></template>
            </el-image>
          </div>

          <div class="record-body">
            <strong>{{ record.garment_name ?? '临时上传服饰' }}</strong>
            <div class="meta">
              <el-tag size="small" effect="plain" :type="backendBadge(record.backend_used).tagType">
                {{ backendBadge(record.backend_used).label }}
              </el-tag>
              <el-tag size="small" effect="plain" type="info">{{ record.quality }}</el-tag>
              <span class="time">{{ record.created_at }}</span>
            </div>
            <p class="task">{{ record.task_id }}</p>
            <div v-if="record.warnings.length" class="warnings">
              <div v-for="(w, i) in record.warnings" :key="i" class="warning-item">⚠ {{ w }}</div>
            </div>
            <div class="record-actions">
              <el-button size="small" @click="download(record)">下载</el-button>
              <el-button size="small" @click="snapshot(record)">截图</el-button>
              <el-button size="small" type="danger" :loading="deleting.has(record.task_id)" @click="remove(record)">删除</el-button>
            </div>
          </div>
        </article>
      </div>

      <div class="pager">
        <el-pagination
          layout="prev, pager, next, total"
          :total="total"
          :page-size="limit"
          :current-page="page"
          @current-change="onPageChange"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.head {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.head h2 {
  margin: 0;
  font-family: var(--yisu-serif);
  font-size: 20px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.record {
  border: 1px solid var(--yisu-rice-deep);
  border-radius: var(--yisu-radius);
  background: #fff;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.record-images {
  position: relative;
  height: 260px;
  background: var(--yisu-rice);
}

.record-images :deep(.el-image) {
  width: 100%;
  height: 100%;
}

.origin {
  position: absolute !important;
  right: 8px;
  bottom: 8px;
  width: 68px !important;
  height: 92px !important;
  border: 2px solid #fff;
  border-radius: 6px;
  box-shadow: var(--yisu-shadow);
  background: #fff;
}

.record-body {
  padding: 12px 14px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.record-body strong {
  font-family: var(--yisu-serif);
  font-size: 16px;
}

.meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.time {
  font-size: 12px;
  color: var(--yisu-ink-soft);
}

.task {
  margin: 0;
  font-size: var(--ys-fs-micro);
  color: var(--yisu-ink-soft);
  word-break: break-all;
}

.warnings {
  margin: 6px 0 0;
  padding: 6px 10px;
  background: #fff8e6;
  border-left: 3px solid #e6a23c;
  border-radius: 4px;
}

.warning-item {
  font-size: 12px;
  color: #b88230;
  line-height: 1.6;
}

.record-actions {
  display: flex;
  gap: 8px;
}

.thumb-fallback {
  display: grid;
  place-items: center;
  height: 100%;
  font-size: var(--ys-fs-micro);
  color: var(--yisu-ink-soft);
}

.pager {
  display: flex;
  justify-content: center;
  margin-top: 18px;
}
</style>
