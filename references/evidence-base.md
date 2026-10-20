# 研究依据与先例地图

## 结论

机器生成文本检测可以提供受条件约束的统计信号，但不能稳定回答“这份简历有多少百分比由 AI 写成”。短文本、未知模型、人工改写、翻译和分布变化都会削弱可靠性；招聘场景还会放大误报的不利影响。因此，本技能不内置作者分类器，而把检测研究转化为可解释线索、替代解释和内容核验动作。

## 直接与相邻方案

| 方案 | 类型 | 可复用部分 | 不能直接复用的原因 |
|---|---|---|---|
| [Pangram for recruiters](https://www.pangram.com/use-cases/recruiters) | 招聘商业产品 | 招聘材料是独立使用场景 | 商业准确率声明不能替代岗位内校准与公平性验证 |
| [RAID](https://github.com/liamdugan/raid) | 大规模检测基准 | 跨模型、领域、攻击和解码设置评测 | 基准不等于对任意简历的可靠作者鉴定 |
| [Binoculars](https://github.com/ahans30/Binoculars) | 零样本检测方法 | 对比语言模型得分的研究路径 | 依赖模型与阈值，短文本和分布外材料仍需校准 |
| [DetectGPT](https://github.com/eric-mitchell/detect-gpt) / [Fast-DetectGPT](https://github.com/baoguangsheng/fast-detect-gpt) | 概率曲率方法 | 无需专门训练的检测思路 | 依赖可用模型概率，跨模型和改写鲁棒性有限 |
| [Ghostbuster](https://github.com/vivek3141/ghostbuster) | 特征与分类器方法 | 多层特征而非单一困惑度 | 训练分布与目标简历不同，不能直接迁移结论 |
| [Turnitin AI writing guidance](https://help.turnitin.com/ai-writing-detection.htm) | 实际产品边界 | 明确要求人工判断、不得单独用于不利行动 | 教育场景不同，但“检测信号不是裁决”可迁移 |

## 关键研究约束

1. **分布外与对抗鲁棒性不足**：[RAID 论文](https://arxiv.org/abs/2405.07940) 在多模型、多领域、解码策略和攻击下测试检测器，显示未知条件和改写会显著影响表现。
2. **改写可破坏检测**：[Can AI-Generated Text be Reliably Detected?](https://arxiv.org/abs/2303.11156) 讨论了递归改写对水印、神经分类器和零样本检测的影响。
3. **非母语写作存在误报风险**：[GPT detectors are biased against non-native English writers](https://arxiv.org/abs/2304.02819) 发现多种检测器会把大量真实的非母语英语文本误判为机器生成。
4. **方法有效性依赖条件**：[Binoculars](https://proceedings.mlr.press/v235/hans24a.html)、[DetectGPT](https://arxiv.org/abs/2301.11305) 和 [Fast-DetectGPT](https://arxiv.org/abs/2310.05130) 都给出了有价值的方法，但没有把任意短简历变成可证明的作者身份结论。
5. **产品方也要求人类复核**：[Turnitin](https://guides.turnitin.com/hc/en-us/articles/28457596598925-AI-writing-detection-in-the-classic-report-view) 明确说明模型可能误判人类、AI 和 AI 改写文本，检测结果不应成为不利行动的唯一依据。

## 采用的设计模式

- 用离散证据等级，不给伪精确百分比；
- 把“文本形态”与“经历是否可信”拆成两个轴；
- 每条线索强制给出替代解释；
- 高影响声明才进入优先核验，避免把风格偏好变成筛选标准；
- 统一结构化问题，减少对特定候选人的选择性怀疑；
- 本地、零依赖特征提取优先，第三方上传必须另行授权；
- 检测信号只触发进一步核验，不触发自动拒绝。

## 巨人肩膀裁决

**裁决：从零构建招聘核验 Skill，而不是复刻通用 AI 文本检测器。**

可复用的是检测研究的失败模式、评测思想和“信号而非裁决”边界；真正需要补齐的是招聘场景中的岗位影响、替代解释、公平追问和人工决策闭环。
