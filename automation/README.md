# n8n Automation Workflows

This directory contains exported n8n workflow configuration files (`.json`) and documentation for the automation pipelines integrated within the Golden Star Agency SaaS travel platform.

## Workflows Included

1. **AI Chatbot Handler (`chatbot-handler.json`)**
   - **Trigger**: Webhook from front-end widget or chat gateway.
   - **Action**: Processes conversational flow, queries FastAPI vector database, and sends reply or alerts support agent.

2. **Lead Notification Agent (`lead-notification.json`)**
   - **Trigger**: Customer contact form or flight quote request.
   - **Action**: Extracts data, filters spam, registers lead in Django, and broadcasts SMS/WhatsApp alert to Super Admins.

3. **Booking Status Broadcast (`booking-status-broadcast.json`)**
   - **Trigger**: Payment success hook or admin reservation status transition.
   - **Action**: Generates PDF invoice/travel voucher, sends email confirmation, and notifies the referring Agent about commission updates.

4. **Content Auto-Publish (`content-auto-publish.json`)**
   - **Trigger**: Super Admin CMS publishing new blogs or packages.
   - **Action**: Formats post, checks SEO tags, and auto-posts previews to official social media channels.

## How to Import Workflows

1. Open your n8n dashboard (usually running on port `5678`).
2. Click **Workflows** &rarr; **Add Workflow**.
3. Select **Import from File** from the top right menu options.
4. Upload any of the JSON files in this directory to load the full node configuration mapping.
