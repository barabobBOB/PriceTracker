import json

from kafka import KafkaProducer
from .set_up import setup_logging


def produce_to_kafka(data: dict) -> None:
    logger = setup_logging()
    logger.info("Kafka producer를 생성합니다.")
    producer = KafkaProducer(
        bootstrap_servers='kafka:29092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    try:
        if data:
            logger.info("데이터를 Kafka 토픽으로 전송합니다: %s", data)
            producer.send('coupang_crawling_topic', value=data)
            logger.info("Kafka로 데이터 전송을 플러시합니다.")
            producer.flush()
            logger.info("데이터 전송이 성공적으로 완료되었습니다.")
    except Exception as e:
        logger.error("Kafka로 데이터 전송 중 오류 발생: %s", e)
    finally:
        logger.info("Kafka producer를 닫습니다.")
        producer.close()
