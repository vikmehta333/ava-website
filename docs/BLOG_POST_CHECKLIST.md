# BLOG POST CREATION CHECKLIST - DO NOT FORGET

**Date:** March 19, 2026  
**Purpose:** Ensure consistent, complete blog post creation every time

---

## ✅ CRITICAL STEPS - MUST FOLLOW

### 1. CONTENT PREPARATION
- [ ] Write blog post content (1,500-2,500 words)
- [ ] Include emojis in headings (📊, ✅, 🚀, etc.)
- [ ] Add FAQ section at end
- [ ] Include CTA section with `id="cta"`
- [ ] Write meta description (under 160 chars)

### 2. HTML TEMPLATE STRUCTURE
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[PAGE TITLE] | Ava Digital</title>
    <meta name="description" content="[META DESCRIPTION]">
    <link rel="canonical" href="https://avadigitalagency.com/[SLUG]/">
    <style>
        /* CRITICAL: All headings must be WHITE */
        h1, h2, h3 { color: white; }
        .hero h1 { color: white; }
        
        /* Rest of CSS from template... */
    </style>
</head>
<body>
    <nav><!-- Logo + Book a Call button --></nav>
    <div class="hero"><!-- Badge, H1 (white!), subtitle, CTA --></div>
    <section><!-- Content with emojis --></section>
    <div class="cta-box" id="cta"><!-- CTA section --></div>
    <section><!-- FAQ items --></section>
    <footer><!-- Full footer --></footer>
</body>
</html>
```

### 3. WORDPRESS PUBLISHING
- [ ] Use `elementor_canvas` template
- [ ] Set proper slug (URL-friendly)
- [ ] Status: `publish`
- [ ] Clear Elementor meta if needed

### 4. BLOG INDEX UPDATE
- [ ] Add new blog card to `/blog/` page
- [ ] Include badge, title, excerpt, link
- [ ] Test both desktop and mobile view

### 5. TESTING CHECKLIST
- [ ] Page loads without errors
- [ ] All headings are WHITE (visible on dark background)
- [ ] Navigation works
- [ ] CTA button links to `/contact`
- [ ] Blog index shows new post
- [ ] Mobile responsive

---

## 📋 REQUIRED ELEMENTS

### Every Blog Post MUST Have:
1. **Navigation bar** with "ava digital" logo + "Book a Call →"
2. **Hero section** with:
   - Badge (📚 Guide, 🤖 AI Marketing, etc.)
   - H1 title (WHITE text!)
   - Subtitle
   - CTA button
3. **Content sections** with emojis in H2/H3
4. **CTA box** with `id="cta"` for nav link
5. **FAQ section** (minimum 3-5 questions)
6. **Full footer** with Services, Cities, Company links

### CSS Critical Rules:
```css
h1, h2, h3 { color: white; }  /* NEVER FORGET THIS */
.hero h1 { color: white; }     /* CRITICAL */
```

---

## 🔗 URLs & RESOURCES

### Live Blog Posts:
1. How to Choose a Digital Marketing Agency  
   https://avadigitalagency.com/how-to-choose-digital-marketing-agency/

2. AI Marketing ROI Calculator  
   https://avadigitalagency.com/ai-marketing-roi-calculator-2/

### Blog Index:
https://avadigitalagency.com/blog/

### WordPress Credentials:
- Username: `vikmehta`
- App Password: `Ivx0 otYS SAJO 3iLS xpVi 9KyW`
- API Endpoint: `https://avadigitalagency.com/wp-json/wp/v2/pages`

---

## 🚨 COMMON MISTAKES TO AVOID

1. **Dark headings on dark background** → Always set `color: white`
2. **Missing CTA id** → Must have `id="cta"` for nav button
3. **Wrong template** → Must use `elementor_canvas`
4. **No FAQ section** → Every post needs FAQs
5. **Forgetting blog index** → Always add to `/blog/` page
6. **No emojis** → Use emojis in headings for visual interest

---

## 📝 NEXT BLOG POST TOPICS (Queue)

1. **LinkedIn Lead Generation Playbook** (260 searches, KD 30)
2. **Naperville Local SEO Guide** 
3. **Outbound Email Strategy Framework**
4. **AI Agent Use Cases for Small Business**

---

## 📞 SUPPORT

If stuck, reference:
- `PAGE_CREATION_GUIDE.md` (full documentation)
- Existing blog posts as templates
- This checklist

**DO NOT PUBLISH WITHOUT CHECKING EVERY BOX ABOVE**

---

Last Updated: March 19, 2026  
Created By: Lola
