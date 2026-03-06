import {
  InsightResponse as InsightResponseType,
  InsightValueData,
  InsightDistributionData,
  InsightListData,
  InsightComparisonData,
  InsightTimelineData,
  Card,
} from '../../api/client';
import { InsightValueRenderer } from './InsightValueRenderer';
import { InsightDistributionRenderer } from './InsightDistributionRenderer';
import { InsightListRenderer } from './InsightListRenderer';
import { InsightComparisonRenderer } from './InsightComparisonRenderer';
import { InsightTimelineRenderer } from './InsightTimelineRenderer';

interface Props {
  response: InsightResponseType;
  onCardClick?: (card: Card) => void;
  /**
   * When true, suppresses the question heading and outer card wrapper.
   * Used when a parent component (e.g. InsightResultCard) already renders
   * the question and wrapper chrome.
   */
  hideQuestion?: boolean;
}

export function InsightResponse({ response, onCardClick, hideQuestion = false }: Props) {
  const { response_type, data, answer_text } = response;

  const renderers = (
    <>
      {response_type === 'value' && (
        <InsightValueRenderer
          data={data as InsightValueData}
          answerText={answer_text}
        />
      )}
      {response_type === 'distribution' && (
        <InsightDistributionRenderer
          data={data as InsightDistributionData}
          answerText={answer_text}
        />
      )}
      {response_type === 'list' && (
        <InsightListRenderer
          data={data as InsightListData}
          answerText={answer_text}
          onCardClick={onCardClick}
        />
      )}
      {response_type === 'comparison' && (
        <InsightComparisonRenderer
          data={data as InsightComparisonData}
          answerText={answer_text}
        />
      )}
      {response_type === 'timeline' && (
        <InsightTimelineRenderer
          data={data as InsightTimelineData}
          answerText={answer_text}
        />
      )}
    </>
  );

  if (hideQuestion) {
    return <>{renderers}</>;
  }

  return (
    <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl border border-gray-100 dark:border-gray-600">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
        {response.question}
      </h3>
      {renderers}
    </div>
  );
}
