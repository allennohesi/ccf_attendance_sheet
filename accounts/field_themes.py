# Shared Tailwind class strings for form widgets
TW_INPUT = (
    "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 "
    "shadow-sm placeholder:text-slate-400 focus:border-brand-600 focus:outline-none focus:ring-2 "
    "focus:ring-brand-600/15 min-h-[2.75rem] transition"
)
TW_SELECT = (
    "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 "
    "shadow-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-600/15 "
    "transition"
)
TW_TEXTAREA = (
    "w-full min-h-28 rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm "
    "text-slate-800 shadow-sm placeholder:text-slate-400 focus:border-brand-600 focus:outline-none "
    "focus:ring-2 focus:ring-brand-600/15 transition"
)
TW_FILE = (
    "block w-full text-sm text-slate-600 file:mr-4 file:cursor-pointer file:rounded-lg file:border-0 "
    "file:bg-brand-50 file:px-4 file:py-2.5 file:text-sm file:font-semibold file:text-brand-700 "
    "file:transition hover:file:bg-brand-100"
)
TW_SELECT_MULTI_ROLES = TW_SELECT + " min-h-40"
