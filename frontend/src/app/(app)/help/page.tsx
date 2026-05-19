"use client"

import { useState } from "react"
import {
  BookOpen,
  MessageSquare,
  Database,
  FlaskConical,
  Settings,
  ChevronDown,
  ChevronRight,
  HelpCircle,
  Zap,
  Shield,
  Keyboard,
} from "lucide-react"

interface FAQItem {
  question: string
  answer: string
}

interface Section {
  title: string
  icon: React.ReactNode
  items: FAQItem[]
}

const sections: Section[] = [
  {
    title: "快速入门",
    icon: <Zap className="w-5 h-5" />,
    items: [
      {
        question: "如何开始使用 AgentStudio？",
        answer:
          "1. 注册账号并登录\n2. 创建或选择一个工作区\n3. 进入「知识库」上传文档\n4. 在「聊天」页面开始与 AI 对话\n\n系统会自动根据上传的文档进行智能问答。",
      },
      {
        question: "如何创建知识库？",
        answer:
          "1. 点击左侧导航「知识库」\n2. 点击右上角「新建知识库」按钮\n3. 输入名称和描述\n4. 上传 PDF、DOCX、MD、TXT 或 HTML 文件\n5. 等待文档处理完成即可使用",
      },
      {
        question: "支持哪些文件格式？",
        answer: "目前支持以下格式：\n• PDF 文档 (.pdf)\n• Word 文档 (.docx)\n• Markdown 文档 (.md)\n• 纯文本文件 (.txt)\n• HTML 网页 (.html)\n\n单个文件建议不超过 10MB。",
      },
    ],
  },
  {
    title: "知识库管理",
    icon: <Database className="w-5 h-5" />,
    items: [
      {
        question: "什么是多路召回？",
        answer:
          "多路召回是指同时使用多种检索方式获取相关内容：\n\n• 向量检索：基于语义相似度\n• BM25 检索：基于关键词匹配\n• GraphRAG：基于知识图谱关联\n\n系统会自动融合多种召回结果，提高检索准确性。",
      },
      {
        question: "如何调整检索参数？",
        answer:
          "在知识库详情页点击「检索调试」可以：\n\n• 调整 Top K（返回结果数量）\n• 调整 Recall K（召回候选数量）\n• 开启/关闭重排序\n• 查看检索结果和分数",
      },
      {
        question: "文档处理失败怎么办？",
        answer:
          "常见原因：\n• 文件格式不支持或损坏\n• 文件过大超过限制\n• 文件内容为空或编码异常\n\n建议：\n• 尝试重新上传\n• 检查文件是否可正常打开\n• 联系管理员查看日志",
      },
    ],
  },
  {
    title: "对话功能",
    icon: <MessageSquare className="w-5 h-5" />,
    items: [
      {
        question: "如何选择知识库进行对话？",
        answer:
          "在聊天页面顶部，点击知识库选择器，选择要使用的知识库。选择后，AI 会基于该知识库的内容回答问题。",
      },
      {
        question: "如何查看引用来源？",
        answer:
          "AI 回复中会显示引用标记 [1], [2] 等。点击引用标记可以查看原始文档片段和来源信息。",
      },
      {
        question: "支持语音输入吗？",
        answer:
          "支持！点击输入框右侧的麦克风按钮即可开始语音输入。系统会自动将语音转文字并填入输入框。\n\n注意：需要浏览器授权麦克风权限。",
      },
      {
        question: "如何清空对话历史？",
        answer:
          "在侧边栏对话列表中，找到要删除的对话，点击右侧的删除按钮即可。也可以点击「新对话」开始新的聊天。",
      },
    ],
  },
  {
    title: "评测系统",
    icon: <FlaskConical className="w-5 h-5" />,
    items: [
      {
        question: "评测指标有哪些？",
        answer:
          "系统提供三个评测指标：\n\n• 语义相似度 (40%)：期望答案与实际答案的语义相似程度\n• 忠实度 (35%)：回答是否基于检索内容，无幻觉\n• 相关性 (25%)：回答与问题的相关程度\n\n综合分数 ≥ 0.7 视为通过。",
      },
      {
        question: "如何创建评测用例？",
        answer:
          "1. 进入「评测」页面\n2. 点击「新建用例」\n3. 输入问题和期望答案\n4. 可选：添加标签分类\n\n创建后可以单条运行或批量运行评测。",
      },
      {
        question: "如何批量运行评测？",
        answer:
          "1. 创建多个评测用例\n2. 点击「批量运行」\n3. 选择要运行的用例和数据集\n4. 选择知识库\n5. 等待评测完成查看结果",
      },
    ],
  },
  {
    title: "工作区与设置",
    icon: <Settings className="w-5 h-5" />,
    items: [
      {
        question: "什么是工作区？",
        answer:
          "工作区是数据和资源的隔离单元。每个工作区有独立的知识库、对话记录和评测数据。\n\n适合多项目或多团队使用同一平台的场景。",
      },
      {
        question: "如何切换工作区？",
        answer:
          "点击左上角的工作区选择器，可以：\n• 查看所有工作区\n• 切换当前工作区\n• 创建新工作区\n• 编辑或删除工作区",
      },
      {
        question: "如何修改个人信息？",
        answer: "目前暂不支持修改个人信息。如需修改邮箱或用户名，请联系管理员。",
      },
    ],
  },
  {
    title: "安全与隐私",
    icon: <Shield className="w-5 h-5" />,
    items: [
      {
        question: "数据安全如何保障？",
        answer:
          "• 所有数据存储在本地数据库\n• API 通信使用 JWT 认证\n• 工作区数据隔离\n• 支持部署在内网环境",
      },
      {
        question: "API Key 如何存储？",
        answer:
          "OpenAI API Key 等敏感信息存储在服务端环境变量中，不会暴露给前端。建议定期轮换密钥。",
      },
    ],
  },
  {
    title: "快捷键",
    icon: <Keyboard className="w-5 h-5" />,
    items: [
      {
        question: "有哪些快捷键？",
        answer:
          "对话页面：\n• Enter：发送消息\n• Shift + Enter：换行\n• Esc：取消语音输入\n\n通用：\n• Ctrl/Cmd + K：快速搜索（开发中）",
      },
    ],
  },
]

function FAQSection({
  section,
  defaultOpen = false,
}: {
  section: Section
  defaultOpen?: boolean
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen)
  const [openItems, setOpenItems] = useState<Set<number>>(new Set())

  const toggleItem = (index: number) => {
    const newSet = new Set(openItems)
    if (newSet.has(index)) {
      newSet.delete(index)
    } else {
      newSet.add(index)
    }
    setOpenItems(newSet)
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors"
      >
        <span className="text-indigo-600">{section.icon}</span>
        <span className="font-medium text-gray-900">{section.title}</span>
        <span className="ml-auto text-gray-400 text-sm">{section.items.length} 个问题</span>
        {isOpen ? (
          <ChevronDown className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronRight className="w-5 h-5 text-gray-400" />
        )}
      </button>

      {isOpen && (
        <div className="border-t border-gray-100">
          {section.items.map((item, index) => (
            <div key={index} className="border-b border-gray-50 last:border-b-0">
              <button
                onClick={() => toggleItem(index)}
                className="w-full flex items-start gap-2 px-4 py-3 hover:bg-gray-50 transition-colors text-left"
              >
                <HelpCircle className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-700 flex-1">{item.question}</span>
                {openItems.has(index) ? (
                  <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
                )}
              </button>
              {openItems.has(index) && (
                <div className="px-4 pb-3 pl-10">
                  <p className="text-sm text-gray-600 whitespace-pre-wrap">{item.answer}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function HelpPage() {
  return (
    <div className="h-full overflow-auto bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-indigo-100 mb-4">
            <BookOpen className="w-7 h-7 text-indigo-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">帮助中心</h1>
          <p className="text-gray-500">了解如何使用 AgentStudio 的各项功能</p>
        </div>

        {/* FAQ Sections */}
        <div className="space-y-4">
          {sections.map((section, index) => (
            <FAQSection key={section.title} section={section} defaultOpen={index === 0} />
          ))}
        </div>

        {/* Footer */}
        <div className="mt-8 p-4 bg-indigo-50 rounded-xl border border-indigo-100">
          <h3 className="font-medium text-indigo-900 mb-2">还有其他问题？</h3>
          <p className="text-sm text-indigo-700">
            如果以上内容没有解决您的问题，请联系管理员或提交 Issue 获取帮助。
          </p>
        </div>
      </div>
    </div>
  )
}
