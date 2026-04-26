import {
  Atom,
  Dna,
  Earth,
  FlaskConical,
  Leaf,
  Microscope,
  Sparkles,
  Telescope
} from "lucide-react";

interface SidebarProps {
  selectedCategory: string;
  onSelectCategory: (category: string) => void;
}

const categories = [
  { id: "all", name: "All Topics", icon: Sparkles },
  { id: "physics", name: "Physics", icon: Atom },
  { id: "chemistry", name: "Chemistry", icon: FlaskConical },
  { id: "biology", name: "Biology", icon: Microscope },
  { id: "earth", name: "Earth Science", icon: Earth },
  { id: "astronomy", name: "Astronomy", icon: Telescope },
  { id: "genetics", name: "Genetics", icon: Dna },
  { id: "ecology", name: "Ecology", icon: Leaf }
];

export default function Sidebar({ selectedCategory, onSelectCategory }: SidebarProps) {
  return (
    <div className="w-64 bg-slate-900 border-r border-slate-700 flex flex-col">
      <div className="p-6 border-b border-slate-700">
        <h1 className="text-xl text-white flex items-center gap-2">
          <Atom className="text-blue-400" size={24} />
          ScienceAI
        </h1>
        <p className="text-sm text-slate-400 mt-1">Chiron - AI Architect Assistant</p>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {categories.map((category) => {
          const Icon = category.icon;
          return (
            <button
              key={category.id}
              onClick={() => onSelectCategory(category.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                selectedCategory === category.id
                  ? "bg-blue-600 text-white"
                  : "text-slate-300 hover:bg-slate-800"
              }`}
            >
              <Icon size={20} />
              <span>{category.name}</span>
            </button>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-700">
        <div className="bg-slate-800 rounded-lg p-4">
          <p className="text-xs text-slate-400">
            Ask questions about any scientific topic and get detailed, educational responses.
          </p>
        </div>
      </div>
    </div>
  );
}
