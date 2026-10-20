# 研究依据与先例扫描

## 裁决

现成通用检测器不适合直接承担招聘判断。这个 Skill 采用“构建辅助核验流程”的路线：文本检测只提供弱线索，核心价值来自内容一致性、替代解释、结构化追问与人类复核。

## 直接与相邻先例

| 先例 | 发现 | 对本 Skill 的启发 |
|---|---|---|
| [DetectRL](https://github.com/junchaoIU/DetectRL) / [论文](https://arxiv.org/abs/2410.23746) | 真实场景基准覆盖多种模型、攻击和文本长度；零样本方法在现实分布上明显下降 | 不把单一检测器当事实来源 |
| [Binoculars](https://github.com/ahans30/Binoculars) / [论文](https://arxiv.org/abs/2401.12070) | 代表性的零样本文本检测方法，需要成对语言模型计算 | 可作为研究参照，不适合作为无条件招聘门槛 |
| [RAID](https://arxiv.org/abs/2405.07940) | 跨模型、领域、采样与对抗改写的大型基准显示检测器容易受分布变化影响 | 必须考虑改写、领域和语言偏移 |
| [Can AI-Generated Text be Reliably Detected?](https://arxiv.org/abs/2303.11156) | 递归改写可显著削弱水印、神经分类器和零样本方法 | 不能承诺稳定识别“AI 含量” |
| [GPT detectors are biased against non-native English writers](https://arxiv.org/abs/2304.02819) | 多个检测器把大量非母语英文误判为 AI 文本 | 禁止把低困惑度、简洁英文或语言背景当负面信号 |
| [SynthID Text](https://deepmind.google/science/synthid/ai-generated-text/) | 水印需在生成时嵌入，识别能力依赖具体生成链路 | 可靠来源证据与通用风格推断必须分开 |
| [DetectGPT](https://github.com/eric-mitchell/detect-gpt) / [Fast-DetectGPT](https://github.com/baoguangsheng/fast-detect-gpt) | 用概率曲率做零样本检测，依赖可访问的语言模型概率 | 不能把特定模型条件下的统计信号迁移成任意短简历的作者证明 |
| [Ghostbuster](https://github.com/vivek3141/ghostbuster) | 用多层特征和分类器检测机器文本 | 训练分布与简历体裁不同，固定特征也容易学习文风代理变量 |

GitHub 上以“resume AI detector”为名的直接项目大多是低成熟度 Demo，常把通用文本分类或异常检测直接套到简历，缺少招聘公平性、候选人核验和高风险决策护栏。没有发现成熟开源方案同时解决“AI 辅助信号 + 经历真实性核验 + HR 可执行追问”。

## 高风险使用原则

- [ACM 关于生成式 AI 内容检测的声明](https://www.acm.org/public-policy/ustpc/ustpc-gai-detection)指出，高风险场景不宜根据检测结果自动拒绝提交，最终准确性应由人判断；其举例包含申请材料。
- [英国 ICO 招聘自动化决策指引](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/employment/recruitment-and-selection/automated-decision-making-and-profiling-for-recruitment-and-selection/)要求对招聘 AI 的高风险个人数据处理进行评估，并记录处理关系与责任。
- [纽约市关于自动化就业决策工具的说明](https://portal.311.nyc.gov/article/?kanumber=KA-03552)要求适用工具进行偏差审计、公开结果并通知候选人。不同地区要求不同，部署方仍需进行本地法律审查。

## 可复用的共同模式

1. 把风格分类结果当置信线索，而不是作者证明。
2. 明确区分检测器内部分数、现实世界基准表现和具体使用阈值。
3. 对短文本、跨语言、专业体裁、编辑后文本降低结论强度。
4. 用来源水印或修订记录确认生成链路；没有来源证据时保持不确定。
5. 在高风险场景保留人类复核、申诉和一致的核验流程。

## 本 Skill 的差异

它不再追求“识别作者是人还是机器”，而是帮助 HR 回答三个更可靠的问题：

1. 哪些表达只与 AI 辅助相容、不能过度解读；
2. 哪些内容缺口真正值得在招聘中核验；
3. 怎样用一致、中性的问题取得更强证据。

因此它不依赖特定模型、API 或检测器，可在任何能读取 Markdown 指令的 Agent 中运行。
