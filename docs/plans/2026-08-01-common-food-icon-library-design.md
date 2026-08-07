# Common Food Icon Library Design

**Date:** 2026-08-01  
**Status:** Approved  
**Product:** Fridge Pal

## Objective

Expand the curated Food Token registry from 16 keys into a coherent household-food icon library. The approved batch contains 70 familiar fresh foods, with stronger coverage of Chinese vegetables and fruit. Production assets remain deterministic Vue-rendered SVG; generated bitmap imagery is not part of the production path.

The existing `rice` and `pasta` keys remain as compatibility-only icons so previously stored food definitions continue to render, but they are not part of the approved fresh-food batch.

## Scope and taxonomy

This batch covers foods a household commonly stores or cooks with. It deliberately excludes broad or differently classified concepts such as mixed beans, olive oil, nuts, rice, pasta, and bread from the new-food set. Staples, condiments, and snacks can receive separate icon groups later.

### Vegetables, fungi, and fresh aromatics — 38

| English | Simplified Chinese | Visual key |
|---|---|---|
| Spinach | 菠菜 | `spinach` |
| Broccoli | 西兰花 | `broccoli` |
| Carrots | 胡萝卜 | `carrots` |
| Tomatoes | 西红柿 | `tomatoes` |
| Onion | 洋葱 | `onion` |
| Garlic | 大蒜 | `garlic` |
| Button mushrooms | 口蘑 | `mushrooms` |
| Peas | 豌豆 | `frozen-peas` |
| Potato | 土豆 | `potato` |
| Sweet potato | 红薯 | `sweet-potato` |
| White radish | 白萝卜 | `white-radish` |
| Lotus root | 莲藕 | `lotus-root` |
| Chinese yam | 山药 | `chinese-yam` |
| Chinese cabbage | 大白菜 | `chinese-cabbage` |
| Baby cabbage | 娃娃菜 | `baby-cabbage` |
| Bok choy | 上海青 | `bok-choy` |
| Lettuce | 生菜 | `lettuce` |
| Chinese leaf lettuce | 油麦菜 | `chinese-leaf-lettuce` |
| Cabbage | 卷心菜 | `cabbage` |
| Celery | 芹菜 | `celery` |
| Celtuce | 莴笋 | `celtuce` |
| Cucumber | 黄瓜 | `cucumber` |
| Eggplant | 茄子 | `eggplant` |
| Green pepper | 青椒 | `green-pepper` |
| Cauliflower | 菜花 | `cauliflower` |
| Pumpkin | 南瓜 | `pumpkin` |
| Winter melon | 冬瓜 | `winter-melon` |
| Green beans | 四季豆 | `green-beans` |
| Shiitake | 香菇 | `shiitake` |
| Enoki | 金针菇 | `enoki` |
| Ginger | 生姜 | `ginger` |
| Scallion | 大葱 | `scallion` |
| Chinese chives | 韭菜 | `chives` |
| Zucchini | 西葫芦 | `zucchini` |
| Loofah | 丝瓜 | `loofah` |
| Bitter melon | 苦瓜 | `bitter-melon` |
| Fresh corn | 鲜玉米 | `corn` |
| Bean sprouts | 豆芽 | `bean-sprouts` |

### Fruit — 18

| English | Simplified Chinese | Visual key |
|---|---|---|
| Apple | 苹果 | `apple` |
| Banana | 香蕉 | `banana` |
| Orange | 橙子 | `orange` |
| Mandarin | 橘子 | `mandarin` |
| Pear | 梨 | `pear` |
| Grapes | 葡萄 | `grapes` |
| Watermelon | 西瓜 | `watermelon` |
| Cantaloupe | 哈密瓜 | `cantaloupe` |
| Strawberry | 草莓 | `strawberry` |
| Blueberries | 蓝莓 | `blueberries` |
| Peach | 桃 | `peach` |
| Mango | 芒果 | `mango` |
| Kiwi | 猕猴桃 | `kiwi` |
| Dragon fruit | 火龙果 | `dragon-fruit` |
| Pineapple | 菠萝 | `pineapple` |
| Pomelo | 柚子 | `pomelo` |
| Lychee | 荔枝 | `lychee` |
| Lemon | 柠檬 | `lemon` |

### Meat, eggs, and aquatic foods — 10

| English | Simplified Chinese | Visual key |
|---|---|---|
| Eggs | 鸡蛋 | `eggs` |
| Chicken breast | 鸡胸肉 | `chicken-breast` |
| Chicken thigh | 鸡腿 | `chicken-thigh` |
| Pork | 猪肉 | `pork` |
| Beef | 牛肉 | `beef` |
| Lamb | 羊肉 | `lamb` |
| Duck | 鸭肉 | `duck` |
| Fish | 鱼 | `fish` |
| Shrimp | 虾 | `shrimp` |
| Crab | 螃蟹 | `crab` |

### Soy and chilled foods — 4

| English | Simplified Chinese | Visual key |
|---|---|---|
| Tofu | 豆腐 | `tofu` |
| Dried tofu | 豆干 | `dried-tofu` |
| Milk | 牛奶 | `milk` |
| Yogurt | 酸奶 | `yogurt` |

## Visual direction: Bold Pantry

Every icon follows one recognition-first semi-flat system:

- Author on a `48 × 48` SVG viewBox with a nominal `4 px` safe area.
- Use one centered ingredient silhouette that occupies roughly 70–82% of the canvas.
- Use two or three dominant flat fills. A small dark detail stroke is allowed only when it materially improves recognition at 24–38 px.
- Light comes from the top left. Highlights are a lighter local color; the bottom-right plane uses a darker local color.
- Use rounded, friendly geometry with a strong outer silhouette and no delicate texture.
- No enclosing circle, square, badge, plate, refrigerator shelf, scenery, face, label, word, gradient, photographic texture, clay rendering, or cast shadow.
- A whole ingredient plus one cut face is allowed only when the cut face is the strongest identifier, such as lotus root, kiwi, watermelon, or dragon fruit.
- Packaging is allowed only where the stored food is primarily recognized by its container at token size: milk, yogurt, and frozen peas. Packaging stays generic and unbranded.
- Raw meat uses clean abstract cuts with no blood, bone fragments, butcher-paper scene, or realistic marbling.
- Icons must remain distinct on white, the warm neutral app canvas, and the neutral Rescue tray.

## Reusable generation prompt

Use this prompt only for future reference-board generation. Production assets must still be normalized into the code-native SVG catalog.

```text
Use case: logo-brand
Asset type: Fridge Pal Food Token reference icon
Primary request: Create one icon of [FOOD NAME / SUBJECT CLAUSE] for the Bold Pantry food-icon family.
Scene/backdrop: isolated object on a completely transparent-looking empty canvas; no environment and no enclosing badge.
Style/medium: recognition-first semi-flat vector illustration, bold friendly silhouette, rounded geometry, crisp scalable edges.
Composition/framing: centered single ingredient, 3/4 or front view chosen for instant recognition, fills 70–82% of a square canvas, at least 8% clear padding on every edge.
Lighting/mood: soft light from the top left expressed only as one simple highlight plane; one darker bottom-right shade plane.
Color palette: two or three saturated but natural food colors; strong contrast on white and warm off-white UI surfaces.
Materials/textures: flat color only; no photographic texture, grain, gloss, translucency, or realistic surface noise.
Constraints: recognizable at 24 px; no text; no logo; no watermark; no face; no plate; no utensils; no scenery; no cast shadow; no gradient; no outline-only drawing. Use at most one cut face when it is essential to recognition. Generic unbranded packaging is allowed only for milk, yogurt, or frozen peas.
Avoid: emoji styling, clay or 3D render, miniature scene, thin details, decorative leaves unrelated to the food, multiple unrelated ingredients, cyberpunk effects.
```

Subject clauses should describe pose and identity, not restate the style. Examples:

- `lotus-root`: “a short diagonal lotus-root segment with one clean round cut face showing its radial holes”
- `bok-choy`: “one compact Shanghai bok choy with a white-green bulb base and three broad dark-green leaves”
- `watermelon`: “one rounded watermelon wedge with a green rind, red flesh, and three large dark seeds”
- `chicken-thigh`: “one clean raw chicken thigh cut with a plump rounded silhouette and a small tapered end, no blood or bone detail”

## Production architecture

- Keep `FoodToken.vue` as the single renderer and preserve monogram/custom-upload behavior.
- Replace the per-file expansion strategy with a data-driven SVG catalog split by category. Each definition contains only deterministic SVG primitives and shared palette constants.
- Build Vue components from those definitions and expose them through the existing `foodIcons` registry.
- Include the 70 approved keys plus compatibility-only `rice` and `pasta` keys in the registry.
- Keep the development token showcase as the visual QA surface for light/tray backgrounds and 24/32/48/64 px size ramps.
- Do not add new database seed inventory or silently mutate existing user food definitions. Admins can assign the new `visualKey` values through the existing Food Library editor.

## Verification

- Add a browser contract first that expects the complete 72-key registry on the development showcase and confirms representative new keys render SVG rather than monograms.
- Typecheck and lint the full frontend.
- Build the production bundle.
- Inspect every icon on light and tray surfaces at 48 px, then inspect representative silhouettes from every category at 24/32/48/64 px.
- Check for clipping, accidental thin strokes, insufficient light-food contrast, duplicate silhouettes, and palette drift.
- Verify the admin icon picker can select at least one newly added visual key and render it in preview.

