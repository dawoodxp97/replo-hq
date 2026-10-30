import { Link } from '@tanstack/react-router';
import type { TutorialListItem } from '@replo/api-client';

type CardItem = Pick<TutorialListItem, 'tutorial_id' | 'title' | 'level' | 'overview' | 'slug' | 'progress_percentage' | 'repo_name'> & { external?: string };

export function TutorialCard({ tutorial }: { tutorial: CardItem }) {
  return (
    <Link to={tutorial.external ?? '/tutorials/$tutorialId'} params={{ tutorialId: tutorial.tutorial_id }} className="block rounded-lg border border-neutral-200 p-4 transition hover:border-neutral-400">
      <div className="flex items-center justify-between">
        <h3 className="font-medium">{tutorial.title}</h3>
        <span className="rounded bg-neutral-100 px-2 py-0.5 text-xs uppercase">{tutorial.level}</span>
      </div>
      {'overview' in tutorial && tutorial.overview ? (
        <p className="mt-2 line-clamp-2 text-sm text-neutral-600">{tutorial.overview}</p>
      ) : null}
      <div className="mt-3 flex items-center justify-between text-xs text-neutral-500">
        <span>{tutorial.repo_name ?? ''}</span>
        {'progress_percentage' in tutorial && typeof tutorial.progress_percentage === 'number' ? (
          <span>{tutorial.progress_percentage}%</span>
        ) : null}
      </div>
    </Link>
  );
}
