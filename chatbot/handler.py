
from django.http import HttpResponse
from .resources import get_resources_by_keyword
from .utils import send_whatsapp_media

resource_map = {
    "1": "hydration",
    "2": "pain",
    "3": "medication",
    "4": "emergency",
    "5": "mental",
    "6": "caregiver"
}

def handle_resource_menu(incoming_msg, profile, msg, response, phone):
    if incoming_msg not in resource_map:
        return None  # Means not handled here

    keyword = resource_map[incoming_msg]
    user_lang = profile.preferred_language if profile else "English"

    results = get_resources_by_keyword(keyword, user_lang)

    if not results.exists():
        msg.body(f"⚠️ Sorry, no resources available for *{keyword.title()}* yet.")
        return HttpResponse(str(response), content_type="application/xml")

    msg.body(f"📎 *Resources for {keyword.title()}*:\n")

    for r in results:
        if r.link:
            msg.body(f"\n🔗 *{r.title}*\n{r.link}")

        if r.file:
            send_whatsapp_media(phone, r.file.url)

    msg.body("\n✅ Reply *menu* to go back.")
    return HttpResponse(str(response), content_type="application/xml")
