"use client"

import { useState, useRef, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import {
  User,
  Mail,
  Camera,
  Check,
  X,
  Loader2,
  ArrowLeft,
  Shield,
  Bell,
  Palette,
} from "lucide-react"
import { useAuthStore } from "@/store/auth"
import { authApi, ApiError } from "@/lib/api"
import clsx from "clsx"

export default function ProfileSettingsPage() {
  const router = useRouter()
  const { user, token } = useAuthStore()

  const [name, setName] = useState(user?.name || "")
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || "")
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (user) {
      setName(user.name)
      setAvatarUrl(user.avatar_url || "")
      setAvatarPreview(user.avatar_url || null)
    }
  }, [user])

  async function handleSave() {
    if (!name.trim()) {
      setError("名称不能为空")
      return
    }

    setSaving(true)
    setError(null)
    setSuccess(false)

    try {
      const updatedUser = await authApi.updateMe({
        name: name.trim(),
        avatar_url: avatarUrl || undefined,
      })

      // Update local storage
      useAuthStore.getState().login = useAuthStore.getState().login
      useAuthStore.setState({
        user: updatedUser,
      })

      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError("保存失败，请重试")
      }
    } finally {
      setSaving(false)
    }
  }

  function handleAvatarChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.type.startsWith("image/")) {
      setError("请选择图片文件")
      return
    }

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      setError("图片大小不能超过 2MB")
      return
    }

    // Read file and convert to base64
    const reader = new FileReader()
    reader.onloadend = () => {
      const base64 = reader.result as string
      setAvatarPreview(base64)
      setAvatarUrl(base64)
    }
    reader.readAsDataURL(file)
  }

  function handleRemoveAvatar() {
    setAvatarPreview(null)
    setAvatarUrl("")
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  const initial = (user?.name || user?.email || "?")[0]?.toUpperCase() || "?"

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <Link
          href="/settings"
          className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft size={16} />
          返回设置
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">个人资料设置</h1>
        <p className="text-gray-500 mt-1">管理您的个人信息和头像</p>
      </div>

      {/* Content */}
      <div className="space-y-6">
        {/* Avatar Section */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">头像</h2>
          <div className="flex items-center gap-6">
            <div className="relative">
              {avatarPreview ? (
                <img
                  src={avatarPreview}
                  alt="头像"
                  className="w-24 h-24 rounded-full object-cover border-4 border-white shadow-lg"
                />
              ) : (
                <div className="w-24 h-24 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-3xl font-bold text-white border-4 border-white shadow-lg">
                  {initial}
                </div>
              )}
              <button
                onClick={() => fileInputRef.current?.click()}
                className="absolute bottom-0 right-0 w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center hover:bg-indigo-700 transition-colors shadow-lg"
                title="上传头像"
              >
                <Camera size={16} />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleAvatarChange}
                className="hidden"
              />
            </div>
            <div className="flex-1">
              <p className="text-sm text-gray-600 mb-2">
                支持 JPG、PNG、GIF 格式，文件大小不超过 2MB
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="px-4 py-2 text-sm font-medium text-indigo-600 border border-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors"
                >
                  上传新头像
                </button>
                {avatarPreview && (
                  <button
                    onClick={handleRemoveAvatar}
                    className="px-4 py-2 text-sm font-medium text-red-600 border border-red-600 rounded-lg hover:bg-red-50 transition-colors"
                  >
                    移除头像
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Name Section */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">基本信息</h2>
          <div className="space-y-4">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <User size={16} className="inline mr-2" />
                显示名称
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="请输入您的名称"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                maxLength={120}
              />
              <p className="mt-1 text-xs text-gray-500">
                {name.length}/120 字符
              </p>
            </div>

            {/* Email (Read-only) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Mail size={16} className="inline mr-2" />
                邮箱地址
              </label>
              <input
                type="email"
                value={user?.email || ""}
                disabled
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg bg-gray-50 text-gray-500 cursor-not-allowed"
              />
              <p className="mt-1 text-xs text-gray-500">邮箱地址不可修改</p>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="flex items-center gap-2 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
            <X size={16} />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {/* Success Message */}
        {success && (
          <div className="flex items-center gap-2 px-4 py-3 bg-green-50 border border-green-200 rounded-lg text-green-700">
            <Check size={16} />
            <span className="text-sm">保存成功！</span>
          </div>
        )}

        {/* Save Button */}
        <div className="flex items-center justify-end gap-3">
          <Link
            href="/settings"
            className="px-6 py-2.5 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            取消
          </Link>
          <button
            onClick={handleSave}
            disabled={saving || !name.trim()}
            className={clsx(
              "px-6 py-2.5 text-sm font-medium text-white rounded-lg transition-colors flex items-center gap-2",
              saving || !name.trim()
                ? "bg-gray-300 cursor-not-allowed"
                : "bg-indigo-600 hover:bg-indigo-700"
            )}
          >
            {saving ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                保存中...
              </>
            ) : (
              <>
                <Check size={16} />
                保存更改
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
