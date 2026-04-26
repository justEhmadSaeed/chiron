import { ArrowRight } from 'lucide-react';

const topics = [
  {
    id: 1,
    title: 'Quantum Mechanics',
    description: 'Explore the fundamental principles of quantum physics and particle behavior',
    gradient: 'from-purple-600 to-blue-600',
  },
  {
    id: 2,
    title: 'Organic Chemistry',
    description: 'Learn about carbon compounds, molecular structures, and reactions',
    gradient: 'from-green-600 to-teal-600',
  },
  {
    id: 3,
    title: 'Cellular Biology',
    description: 'Discover how cells function and maintain life processes',
    gradient: 'from-pink-600 to-rose-600',
  },
  {
    id: 4,
    title: 'Climate Science',
    description: 'Understand Earth\'s climate systems and environmental changes',
    gradient: 'from-blue-600 to-cyan-600',
  },
  {
    id: 5,
    title: 'Astrophysics',
    description: 'Study celestial objects, space, and the universe',
    gradient: 'from-indigo-600 to-purple-600',
  },
  {
    id: 6,
    title: 'Molecular Genetics',
    description: 'Learn about DNA, genes, and heredity mechanisms',
    gradient: 'from-orange-600 to-red-600',
  },
];

export default function TopicCards() {
  return (
    <div className="p-6">
      <h2 className="text-2xl text-white mb-6">Popular Topics</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {topics.map((topic) => (
          <div
            key={topic.id}
            className="bg-slate-800 rounded-xl p-6 hover:bg-slate-750 transition-colors cursor-pointer group border border-slate-700"
          >
            <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${topic.gradient} mb-4 flex items-center justify-center`}>
              <ArrowRight className="text-white" size={24} />
            </div>
            <h3 className="text-white mb-2">{topic.title}</h3>
            <p className="text-sm text-slate-400 mb-4">{topic.description}</p>
            <button className="text-blue-400 text-sm flex items-center gap-2 group-hover:gap-3 transition-all">
              Explore
              <ArrowRight size={16} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
